#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import AppointmentReport
from childcount.models import Encounter
from childcount.exceptions import ParseError, BadValue, InvalidDOB
from childcount.utils import DOBProcessor


class AppointmentForm(CCForm):
    KEYWORDS = {
        'en': ['apt'],
        'fr': ['apt'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected date of "\
                            "appointment"))

        try:
            aptr = AppointmentReport.objects.get(encounter=self.encounter)
        except AppointmentReport.DoesNotExist:
            aptr = AppointmentReport(encounter=self.encounter)
        aptr.form_group = self.form_group

        expected_on_str = ''.join(self.params[1:])
        try:
            #need to trick DOBProcessor: use a future date for date_ref
            date_ref = datetime.today() + timedelta(375)
            expected_on, variance = DOBProcessor.from_dob(self.chw.language, \
                                            expected_on_str, date_ref.date())
        except InvalidDOB:
            raise BadValue(_(u"Could not understand the date of "\
                                "appointment %(expected_on)s" % \
                                {'expected_on': expected_on_str}))
        if expected_on < self.date.date():
            raise BadValue(_(u"%(expected_on)s is already in the past, " \
                            "please use a future date of appointment." % \
                                {'expected_on': expected_on}))
        aptr.appointment_date = expected_on
        aptr.save()
 
        self.response = _(u"Next appointment is on %(expected_on)s.") % \
                            {'expected_on': aptr.appointment_date}
