#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models import Vaccine
from childcount.models.reports import UnderOneReport
from childcount.models.reports import SUnderOne as SauriUnderOneReport
from childcount.exceptions import Inapplicable, ParseError, BadValue
from childcount.forms.utils import MultipleChoiceField


class SauriUnderOneForm(CCForm):
    KEYWORDS = {
        'en': ['t'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        breast_field = MultipleChoiceField()
        breast_field.add_choice('en', UnderOneReport.BREAST_YES, 'Y')
        breast_field.add_choice('en', UnderOneReport.BREAST_NO, 'N')
        breast_field.add_choice('en', UnderOneReport.BREAST_UNKOWN, 'U')

        imm_field = MultipleChoiceField()
        imm_field.add_choice('en', UnderOneReport.IMMUNIZED_YES, 'Y')
        imm_field.add_choice('en', UnderOneReport.IMMUNIZED_NO, 'N')
        imm_field.add_choice('en', UnderOneReport.IMMUNIZED_UNKOWN, 'U')

        try:
            uor = SauriUnderOneReport.objects.get(encounter=self.encounter)
            uor.reset()
        except SauriUnderOneReport.DoesNotExist:
            uor = SauriUnderOneReport(encounter=self.encounter)
        uor.form_group = self.form_group


        breast_field.set_language(self.chw.language)
        imm_field.set_language(self.chw.language)

        days, weeks, months = patient.age_in_days_weeks_months()
        if months > 12:
            raise Inapplicable(_(u"Child is too old for this report"))

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected | breast feeding " \
                                "only | up-to-date immunisations"))

        breast = self.params[1]
        if not breast_field.is_valid_choice(breast):
            raise ParseError(_(u"|Breast feeding only?| must be %(choices)s") \
                             % {'choices': breast_field.choices_string()})
        breast_db = breast_field.get_db_value(breast)

        imm = self.params[2]
        if not imm_field.is_valid_choice(imm):
            raise ParseError(_(u"|Up-to-date Immunisations?| must be " \
                                "%(choices)s") % \
                                {'choices': imm_field.choices_string()})
        imm_db = imm_field.get_db_value(imm)


        uor.breast_only = breast_db
        uor.immunized = imm_db

        vaccine_str = ""
        if len(self.params) > 3:
            vaccines = self.params[3:]
            v_codes = dict([(vaccine.code.upper(), vaccine) \
                             for vaccine in \
                             Vaccine.objects.all()])
            valid = []
            unkown = []
            for v in vaccines:
                obj = v_codes.get(v.upper(), None)
                if obj is not None:
                    valid.append(obj)
                else:
                    unkown.append(v)

            if unkown:
                invalid_str = _(u"Unkown Vaccine code(s): %(codes)s. " \
                                 "UnderOne form not saved.") % \
                                 {'codes': ', '.join(unkown).upper()}
                raise ParseError(invalid_str)
            if valid:
                v_string = ', '.join([v.code for v in valid])
                vaccine_str = _(u". Vaccines: %(vs)s") % {'vs': v_string}
                uor.save()
                for obj in valid:
                    uor.vaccine.add(obj)

        uor.save()

        if breast_db == UnderOneReport.BREAST_YES:
            breast_str = _(u"Exclusive breast feeding")
        elif breast_db == UnderOneReport.BREAST_NO:
            breast_str = _(u"Not exclusive breast feeding")
        elif breast_db == UnderOneReport.BREAST_UNKOWN:
            breast_str = _(u"Unkown if exclusively breast feeding")

        if imm_db == UnderOneReport.IMMUNIZED_YES:
            imm_str = _(u"Up-to-date on immunisations")
        elif imm_db == UnderOneReport.IMMUNIZED_NO:
            imm_str = _(u"Not up-to-date on immunisations")
        elif imm_db == UnderOneReport.IMMUNIZED_UNKOWN:
            imm_str = _(u"Unkown if up-to-date on immunisations")

        self.response = breast_str + ', ' + imm_str + vaccine_str
