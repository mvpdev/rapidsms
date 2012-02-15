#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

import datetime

from django.utils.translation import ugettext as _

from locations.models import Location

from childcount.commands import CCCommand
from childcount.models import Patient, CHW
from childcount.utils import authenticated

class RelocateCommand(CCCommand):
    ''' Relocate a household
        
        Format: reloc LOC_CODE HEALTH_ID

        Relocates the household containing
        the patient HEALTH_ID to location
        LOC_CODE with the current CHW.
    '''

    KEYWORDS = {
        'en': ['reloc'],
        'rw': ['reloc'],
        'fr': ['reloc'],
    }

    LOCATION_MOVED = 'X'

    @authenticated
    def process(self):
        if 'encounter_date' not in self.message.__dict__:
            self.message.respond(_(u'Cannot run reloc command from '
                                    'cell phone. Use the computer interface '
                                    'instead.'), 'error')
            return True

        # warn if no search criteria
        if self.params.__len__() != 3:
            self.message.respond(_(u"Relocate command format: " \
                "reloc LOC HEALTH_ID."),
            'error')
            return True

        # lookup CHW
        try:
            new_chw = CHW.objects.get(pk = self.message.chw)
        except CHW.DoesNotExist:
            self.message.respond(_(u"CHW with ID %(id)d does not exist") % \
                {'id': self.message.chw})
            return True

        loc_code = self.params[1]
        health_id = self.params[2]

        location = None

        # If location code is LOCATION_MOVED, then don't look up
        # the location -- just marked the HH as moved.
        active = (loc_code.upper() != self.LOCATION_MOVED)
            
        # Look up location code if HH is to remain active
        if active:
            try: 
                location = Location.objects.get(code=loc_code)
            except Patient.DoesNotExist:
                self.message.respond(_(u"There is no location with code " \
                                        "%(code)s.") % {'code': loc_code}, 'error')

        # Look up health id
        person = None
        try: 
            person = Patient.objects.get(health_id=health_id)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': health_id}, 'error')

        members = Patient\
            .objects\
            .filter(household__health_id=person.household.health_id)

        msg = u''

        if active:
            # Relocate patients and assign new CHW
            count = members.update(location=location,\
                chw=new_chw,\
                status=Patient.STATUS_ACTIVE)

            msg = _(u"Made status ACTIVE and moved %(count)d people to %(loc)s with CHW %(chw)s: ") % \
                {'loc': location.code.upper(), \
                'chw': new_chw.full_name(), \
                'count': count}
        else:
            # Mark HH members as inactive
            count = members.update(status=Patient.STATUS_INACTIVE)
            msg = _("Marked %(count)d patients as INACTIVE: ") % \
                {'count': count}

        msg += ' '.join([p.health_id.upper() for p in members])

        self.message.respond(msg, 'success')
        return True
