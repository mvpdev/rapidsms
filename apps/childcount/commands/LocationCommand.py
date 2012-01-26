#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

import datetime

from django.utils.translation import ugettext as _

from locations.models import Location

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated

class LocationCommand(CCCommand):
    ''' Change location for a househol
    '''

    KEYWORDS = {
        'en': ['loc'],
        'rw': ['loc'],
        'fr': ['loc'],
    }

    def _relocate_hh(self, loc, hid):
        person = None

        # Lookup health id
        try: 
            person = Patient.objects.get(health_id=hid)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': hid}, 'error')
            return False

        members = Patient.objects.all()\
            .filter(household__health_id = person.household.health_id)
        number = members.update(location = loc)

        id_str = ["%s, " % hid for hid in map(lambda m: m.health_id.upper(), members)]

        self.message.respond(_(u"Set location for %(n)d patient(s) [%(idstr)s] to %(loc)s") \
                                % {'idstr': id_str, 'loc': loc.code, 'n': number}, \
                                'success')
        return True
        
    @authenticated
    def process(self):
        if 'encounter_date' not in self.message.__dict__:
            self.message.respond(_(u'Cannot run loc command from '
                                    'cell phone. Use the computer interface '
                                    'instead.'), 'error')
            return True

        # warn if no search criteria
        if self.params.__len__() < 3:
            self.message.respond(_(u"Location command requires at least a " \
                                    "location code and household ID."),
                                   'error')
            return True

        loc = None
        try:
            loc = Location.objects.get(code = self.params[1].upper())
        except Location.DoesNotExist:
            self.message.respond(_(u"Location with code %(code)s does not exist.") \
                                    % {'code': self.params[1].upper()},\
                                   'error')
            return True
            
        for hid in self.params[2:]:
            self._relocate_hh(loc, hid.upper())
            
        return True
