#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import UnderOneReport
from childcount.exceptions import Inapplicable, ParseError, BadValue
from childcount.forms.utils import MultipleChoiceField


class UnderOneForm(CCForm):
    KEYWORDS = {
        'en': ['t'],
        'fr': ['t'],
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
            uor = UnderOneReport.objects.get(encounter=self.encounter)
            uor.reset()
        except UnderOneReport.DoesNotExist:
            uor = UnderOneReport(encounter=self.encounter)
        uor.form_group = self.form_group

        breast_field.set_language(self.chw.language)
        imm_field.set_language(self.chw.language)

        days, weeks, months = patient.age_in_days_weeks_months()
        if months > 12:
            raise Inapplicable(_(u"Child is too old for this report."))

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: | breast feeding " \
                                "only | up-to-date immunisations |"))

        breast = self.params[1]
        if not breast_field.is_valid_choice(breast):
            raise ParseError(_(u"| Breast feeding only? | must be %(choices)s.") \
                             % {'choices': breast_field.choices_string()})
        breast_db = breast_field.get_db_value(breast)

        imm = self.params[2]
        if not imm_field.is_valid_choice(imm):
            raise ParseError(_(u"| Up-to-date Immunisations? | must be " \
                                "%(choices)s.") % \
                                {'choices': imm_field.choices_string()})
        imm_db = imm_field.get_db_value(imm)

        uor.breast_only = breast_db
        uor.immunized = imm_db
        uor.save()

        if breast_db == UnderOneReport.BREAST_YES:
            breast_str = _(u"Exclusive breast feeding.")
        elif breast_db == UnderOneReport.BREAST_NO:
            breast_str = _(u"Not exclusive breast feeding.")
        elif breast_db == UnderOneReport.BREAST_UNKOWN:
            breast_str = _(u"Unkown if exclusively breast feeding.")

        if imm_db == UnderOneReport.IMMUNIZED_YES:
            imm_str = _(u"Up-to-date on immunisations.")
        elif imm_db == UnderOneReport.IMMUNIZED_NO:
            imm_str = _(u"Not up-to-date on immunisations.")
        elif imm_db == UnderOneReport.IMMUNIZED_UNKOWN:
            imm_str = _(u"Unkown if up-to-date on immunisations.")

        self.response = breast_str + ', ' + imm_str
