#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

import datetime

from django.utils.translation import ugettext as _

from childcount.commands import CCCommand
from childcount.models import Patient, CHW
from childcount.utils import authenticated

class HouseholdHeadCommand(CCCommand):
    ''' Change HHH for a family
    '''

    KEYWORDS = {
        'en': ['changehh'],
        'rw': ['changehh'],
        'fr': ['changehh'],
    }

    @authenticated
    def process(self):
        if 'encounter_date' not in self.message.__dict__:
            self.message.respond(_(u'Cannot run chown command from '
                                    'cell phone. Use the computer interface '
                                    'instead.'), 'error')
            return True

        # warn if no search criteria
        if self.params.__len__() < 3:
            self.message.respond(_(u"Use: changehh patient_id new_hh_id"),'error')
            return True

        # lookup HH
        old_hid = self.params[1]
        new_hid = self.params[2]
        try:
            member = Patient.objects.get(health_id=old_hid)
        except Patient.DoesNotExist:
            self.message.respond(_(u"Patient with ID %(hid)s "\
                                    "does not exist") % \
                {'hid': member.upper()}, 'error')
            return True

        old_hh = member.household

        try:
            new_hh= Patient.objects.get(health_id=new_hid)
        except Patient.DoesNotExist:
            self.message.respond(_(u"Patient with ID %(hid)s "\
                                    "does not exist") % \
                {'hid': new_hid.upper()}, 'error')
            return True

        n = Patient\
            .objects\
            .filter(household__pk=old_hh.pk)\
            .update(household=new_hh)

        self.message.respond(\
            _(u"Changed head of household for %(n)d patients from "\
                "[%(old_hh)s] to [%(new_hh)s]." ) \
                % {'n': n, 'old_hh': old_hh, 'new_hh': new_hh},\
            'success')
        return True

