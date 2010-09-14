#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga
import re

from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group

from CCForm import CCForm
from childcount.models import Encounter
from childcount.models.reports import HIVTestReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField
from childcount.utils import send_msg


class HIVTestForm(CCForm):
    KEYWORDS = {
        'en': ['ht'],
        'fr': ['ht'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        hiv_field = MultipleChoiceField()
        hiv_field.add_choice('en', HIVTestReport.HIV_YES, 'Y')
        hiv_field.add_choice('en', HIVTestReport.HIV_NO, 'N')
        hiv_field.add_choice('en', HIVTestReport.HIV_UNKNOWN, 'U')
        hiv_field.add_choice('en', HIVTestReport.HIV_NOCONSENT, 'NC')

        keyword = self.params[0]

        blood_drawn_field = MultipleChoiceField()
        blood_drawn_field.add_choice('en', \
                                    HIVTestReport.BLOOD_DRAWN_YES, 'Y')
        blood_drawn_field.add_choice('en', \
                                    HIVTestReport.BLOOD_DRAWN_NO, 'N')
        blood_drawn_field.add_choice('en', \
                                    HIVTestReport.BLOOD_DRAWN_UNKNOWN, 'U')
        
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info."))
        try:
            htr = HIVTestReport.objects.get(encounter=self.encounter)
            htr.reset()
        except HIVTestReport.DoesNotExist:
            htr = HIVTestReport(encounter=self.encounter)
        htr.form_group = self.form_group

        hiv_field.set_language(self.chw.language)
        blood_drawn_field.set_language(self.chw.language)

        if not hiv_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"| HIV+ | must be %(choices)s.") % \
                              {'choices': hiv_field.choices_string()})
        hiv = hiv_field.get_db_value(self.params[1])
        
        if hiv == HIVTestReport.HIV_YES and len(self.params) < 3:
            raise ParseError(_(u"Not enough info. You need to answer CD4 "\
                                "question as well."))

        if(len(self.params) > 2):
            if not blood_drawn_field.is_valid_choice(self.params[2]):
                raise ParseError(_(u"| Blood drawn | must be %(choices)s.") % \
                                  {'choices': blood_drawn_field.choices_string()})
            blood_drawn = blood_drawn_field.get_db_value(self.params[2])
            htr.blood_drawn = blood_drawn
        htr.hiv = hiv
        htr.save()
 
        self.response = _(u"HIV Test done.")
        #set patient hiv status
        if htr.hiv == HIVTestReport.HIV_YES:
            patient.hiv_status = True
            patient.save()
        elif htr.hiv == HIVTestReport.HIV_NO:
            patient.hiv_status = False
            patient.save()
        else:
            pass
