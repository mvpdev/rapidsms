#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import AntenatalVisitReport
from childcount.models import Encounter
from childcount.exceptions import ParseError, BadValue, InvalidDOB
from childcount.utils import DOBProcessor
from childcount.forms.utils import MultipleChoiceField


class AntenatalVisitForm(CCForm):
    KEYWORDS = {
        'en': ['iav'],
        'fr': ['iav'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        hiv_field = MultipleChoiceField()
        hiv_field.add_choice('en', AntenatalVisitReport.HIV_YES, 'Y')
        hiv_field.add_choice('en', AntenatalVisitReport.HIV_NO, 'N')
        hiv_field.add_choice('en', AntenatalVisitReport.HIV_UNKNOWN, 'U')

        blood_drawn_field = MultipleChoiceField()
        blood_drawn_field.add_choice('en', \
                                    AntenatalVisitReport.BLOOD_DRAWN_YES, 'Y')
        blood_drawn_field.add_choice('en', \
                                    AntenatalVisitReport.BLOOD_DRAWN_NO, 'N')

        if len(self.params) < 5:
            raise ParseError(_(u"Not enough info."))

        try:
            avr = AntenatalVisitReport.objects.get(encounter=self.encounter)
        except AntenatalVisitReport.DoesNotExist:
            avr = AntenatalVisitReport(encounter=self.encounter)
        avr.form_group = self.form_group

        hiv_field.set_language(self.chw.language)
        blood_drawn_field.set_language(self.chw.language)
        if not self.params[1].isdigit():
            raise ParseError(_(u"Length of pregnancy in weeks" \
                                "must be entered as a number."))

        expected_on_str = self.params[2]
        try:
            #need to trick DOBProcessor: use a future date for date_ref
            date_ref = datetime.today() + timedelta(375)
            expected_on, variance = DOBProcessor.from_dob(self.chw.language, \
                                            expected_on_str, date_ref.date())
        except InvalidDOB:
            raise BadValue(_(u"Could not understand expected date of" \
                             " delivery: %(expected_on)s.") % \
                             {'expected_on': expected_on_str})
        if expected_on < self.date.date():
            raise BadValue(_(u"%(expected_on)s is already in the past, " \
                            "the expected delivery date should be a "\
                            "future date." % \
                                {'expected_on': expected_on}))

        if not hiv_field.is_valid_choice(self.params[3]):
            raise ParseError(_(u"HIV+ must be %(choices)s.") % \
                              {'choices': hiv_field.choices_string()})
        hiv = hiv_field.get_db_value(self.params[3])
        if not blood_drawn_field.is_valid_choice(self.params[4]):
            raise ParseError(_(u"Blood drawn must be %(choices)s.") % \
                              {'choices': blood_drawn_field.choices_string()})
        blood_drawn = blood_drawn_field.get_db_value(self.params[4])
        avr.pregnancy_week = int(self.params[1])
        avr.expected_on = expected_on
        avr.hiv = hiv
        avr.blood_drawn = blood_drawn
        avr.save()
 
        self.response = _(u"%(weeks)d weeks pregnant, expected date of "\
                            "delivery is %(expected_on)s.") % \
                            {'weeks': avr.pregnancy_week, \
                            'expected_on': avr.expected_on}
