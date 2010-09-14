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


class AntenatalVisitForm(CCForm):
    KEYWORDS = {
        'en': ['pf'],
        'fr': ['pf'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info."))

        try:
            avr = AntenatalVisitReport.objects.get(encounter=self.encounter)
        except AntenatalVisitReport.DoesNotExist:
            avr = AntenatalVisitReport(encounter=self.encounter)
        avr.form_group = self.form_group

        expected_on_str = self.params[1]
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
        avr.expected_on = expected_on
        avr.save()
 
        self.response = _(u"Expected date of "\
                            "delivery is %(expected_on)s.") % \
                            {'expected_on': avr.expected_on}
        #reminder to CHW 3 weeks b4 expected date of delivery to send patient
        # to clinic
        msg = _(u"Please send %(patient)s to the health center on for " \
                "their appointment") % \
                {'patient': patient}
