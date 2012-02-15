#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter, Configuration
from childcount.models.reports import UnderOneReport
from childcount.exceptions import Inapplicable, ParseError, BadValue
from childcount.forms.utils import MultipleChoiceField


class UnderOneForm(CCForm):
    """ Under One Report.

    params:
        * Does the mother exclusively breast feed (Y/N/U)
        * Is the child up-to-date onimmunizations? (Y/N/U)
    """

    KEYWORDS = {
        'en': ['t'],
        'rw': ['t'],
        'fr': ['t'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        breast_field = MultipleChoiceField()
        breast_field.add_choice('en', UnderOneReport.BREAST_YES, 'Y')
        breast_field.add_choice('en', UnderOneReport.BREAST_NO, 'N')
        breast_field.add_choice('en', UnderOneReport.BREAST_UNKNOWN, 'U')
        breast_field.add_choice('rw', UnderOneReport.BREAST_YES, 'Y')
        breast_field.add_choice('rw', UnderOneReport.BREAST_NO, 'N')
        breast_field.add_choice('rw', UnderOneReport.BREAST_UNKNOWN, 'U')
        breast_field.add_choice('fr', UnderOneReport.BREAST_YES, 'O')
        breast_field.add_choice('fr', UnderOneReport.BREAST_NO, 'N')
        breast_field.add_choice('fr', UnderOneReport.BREAST_UNKNOWN, 'I')

        imm_field = MultipleChoiceField()
        imm_field.add_choice('en', UnderOneReport.IMMUNIZED_YES, 'Y')
        imm_field.add_choice('en', UnderOneReport.IMMUNIZED_NO, 'N')
        imm_field.add_choice('en', UnderOneReport.IMMUNIZED_UNKNOWN, 'U')
        imm_field.add_choice('rw', UnderOneReport.IMMUNIZED_YES, 'Y')
        imm_field.add_choice('rw', UnderOneReport.IMMUNIZED_NO, 'N')
        imm_field.add_choice('rw', UnderOneReport.IMMUNIZED_UNKNOWN, 'U')
        imm_field.add_choice('fr', UnderOneReport.IMMUNIZED_YES, 'O')
        imm_field.add_choice('fr', UnderOneReport.IMMUNIZED_NO, 'N')
        imm_field.add_choice('fr', UnderOneReport.IMMUNIZED_UNKNOWN, 'I')

        try:
            uor = UnderOneReport.objects.get(encounter=self.encounter)
            uor.reset()
        except UnderOneReport.DoesNotExist:
            uor = UnderOneReport(encounter=self.encounter)
        uor.form_group = self.form_group

        breast_field.set_language(self.chw.language)
        imm_field.set_language(self.chw.language)

        days, weeks, months = patient.age_in_days_weeks_months(\
            self.encounter.encounter_date.date())

        # Allow up to 5 years to CHWs can mark kids over 1 as
        # immunized

        max_age = 12
        try:
            max_age = Configuration.objects.get(\
                key='accept_under_one_report_until_months').value
        except Configuration.DoesNotExist:
            # Don't worry if this Configuration doesn't exist
            pass

        # Make sure we're dealing with an integer
        max_age = int(max_age)

        if months > max_age:
            raise Inapplicable(_(u"This report is only allowed for children "\
                                "under %(max_age)d months. This child is %(age)d "\
                                "months old.") \
                                % {'max_age': max_age, 'age': months})

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
        elif breast_db == UnderOneReport.BREAST_UNKNOWN:
            breast_str = _(u"Unknown if exclusively breast feeding.")

        if imm_db == UnderOneReport.IMMUNIZED_YES:
            imm_str = _(u"Up-to-date on immunisations.")
        elif imm_db == UnderOneReport.IMMUNIZED_NO:
            imm_str = _(u"Not up-to-date on immunisations.")
        elif imm_db == UnderOneReport.IMMUNIZED_UNKNOWN:
            imm_str = _(u"Unknown if up-to-date on immunisations.")

        self.response = breast_str + ', ' + imm_str
