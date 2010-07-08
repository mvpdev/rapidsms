#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Fever Logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from childcount.forms.CCForm import CCForm
from childcount.models import Encounter
from childcount.models.reports import FeverReport
from childcount.forms.utils import MultipleChoiceField
from childcount.exceptions import ParseError, Inapplicable


class FeverForm(CCForm):
    KEYWORDS = {
        'en': ['f'],
        'fr': ['f'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        rdt_field = MultipleChoiceField()
        rdt_field.add_choice('en', FeverReport.RDT_POSITIVE, 'Y')
        rdt_field.add_choice('en', FeverReport.RDT_NEGATIVE, 'N')
        rdt_field.add_choice('en', FeverReport.RDT_UNKOWN, 'U')

        try:
            fr = FeverReport.objects.get(encounter=self.encounter)
            fr.reset()
        except FeverReport.DoesNotExist:
            fr = FeverReport(encounter=self.encounter)
        fr.form_group = self.form_group

        rdt_field.set_language(self.chw.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: %s") % \
                                                rdt_field.choices_string)

        if not rdt_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"RDT Result must be %(choices)s.") % \
                              {'choices': rdt_field.choices_string()})

        days, weeks, months = patient.age_in_days_weeks_months()

        rdt = rdt_field.get_db_value(self.params[1])
        if rdt == FeverReport.RDT_POSITIVE:
            years = patient.years()
            tabs, yage = None, None
            # just reformatted to make it look like less ugh
            if years < 1:
                if months < 2:
                    tabs, yage = None, None
                else:
                    tabs, yage = 1, _("less than 3")
            elif years < 3:
                tabs, yage = 1, _("less than 3")
            elif years < 9:
                tabs, yage = 2, years
            elif years < 15:
                tabs, yage = 3, years
            else:
                tabs, yage = 4, years
            # no tabs means too young
            if not tabs:
                instructions = (_(u"Child is too young for treatment." \
                    " Please refer IMMEDIATELY to clinic."))
            else:
                instructions = _(u"Child is %(age)s. Please provide "\
                                  "%(tabs)s tab%(plural)s of Coartem "\
                                  "(ACT) twice a day for 3 days.") % \
                                   {'age': yage, \
                                    'tabs': tabs, \
                                    'plural': (tabs > 1) and 's' or ''}

            self.response = _("Positive RDT result. ") + instructions

            '''alert = \
                _("MRDT> Child %(last_name)s, %(first_name)s, "\
                "%(gender)s/%(age)s (%(zone)s) has MALARIA%(danger)s. "\
                      "CHW: ..." % info)

            expires_on = datetime.now() + timedelta(7)
            case = Case(patient=patient, expires_on=expires_on, \
                        type=Case.TYPE_FEVER)
            case.save()
            '''
        elif rdt == FeverReport.RDT_NEGATIVE:
            self.response = _(u"Negative RDT result.")
        elif rdt == FeverReport.RDT_UNKOWN:
            self.response = _(u"Unkown RDT result.")

        fr.rdt_result = rdt
        fr.save()
