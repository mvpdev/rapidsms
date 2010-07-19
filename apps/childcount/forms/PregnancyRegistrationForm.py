#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import PregnancyRegistrationReport
from childcount.models import Encounter
from childcount.exceptions import ParseError, BadValue, InvalidDOB
from childcount.utils import DOBProcessor
from childcount.forms.utils import MultipleChoiceField


class PregnancyRegistrationForm(CCForm):
    KEYWORDS = {
        'en': ['prg'],
        'fr': ['prg'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        married_field = MultipleChoiceField()
        married_field.add_choice('en', PregnancyRegistrationReport.MARRIED_YES, 'Y')
        married_field.add_choice('en', PregnancyRegistrationReport.MARRIED_NO, 'N')
        #married_field.add_choice('en', PregnancyRegistrationReport.HIV_UNKNOWN, 'U')

        if len(self.params) < 4:
            raise ParseError(_(u"Not enough info."))

        try:
            prgr = PregnancyRegistrationReport.objects.get(encounter=self.encounter)
        except PregnancyRegistrationReport.DoesNotExist:
            prgr = PregnancyRegistrationReport(encounter=self.encounter)
        prgr.form_group = self.form_group

        married_field.set_language(self.chw.language)
        if not married_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"Married must be %(choices)s.") % \
                              {'choices': married_field.choices_string()})
        married = married_field.get_db_value(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of pregnancies " \
                                "must be entered as a number."))
        if not self.params[3].isdigit():
            raise ParseError(_(u"Number of children alive " \
                                "must be entered as a number."))
        prgr.married = married
        prgr.pregnancies = int(self.params[2])
        prgr.number_of_children = int(self.params[3])
        prgr.save()
        married_str = _(u"married")
        if not married:
            married_str = _(u"not married")
        self.response = _(u"Is %(married)s, has had %(pregnancies)s "\
                            "pregnancies and %(children)s alive.") % \
                            {'married': married_str, \
                            'pregnancies': prgr.pregnancies, \
                            'children': prgr.number_of_children}
