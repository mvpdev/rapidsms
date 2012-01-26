#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

'''
AppointmentForm - Save appointments

Generate a notification 3 week days before appointment date.
Close previous appointment dates
'''

from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Patient
from childcount.models import Configuration
from childcount.models.reports import AppointmentReport
from childcount.models import Encounter
from childcount.exceptions import ParseError, BadValue, InvalidDOB
from childcount.exceptions import Inapplicable
from childcount.utils import DOBProcessor


class AppointmentForm(CCForm):
    """ The status of patients appointment

    Params: 
        * date of appointment
    """

    KEYWORDS = {
        'en': ['ap'],
        'rw': ['ap'],
        'fr': ['ap'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        print self.params
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: date of "\
                            "appointment."))
        days, weeks, months = patient.age_in_days_weeks_months(\
            self.encounter.encounter_date.date())
        years = months / 12
        if (months > 18 and patient.gender == Patient.GENDER_MALE) or \
            (patient.gender == Patient.GENDER_FEMALE and years < 11 and \
                months > 18):
            raise Inapplicable(_(u"Inapplicable: %(patient)s is not within "
                                    "required age bracket" % \
                                    {'patient': patient}))
        try:
            aptr = AppointmentReport.objects.get(encounter=self.encounter)
        except AppointmentReport.DoesNotExist:
            aptr = AppointmentReport(encounter=self.encounter)
        aptr.form_group = self.form_group

        expected_on_str = ''.join(self.params[1:])
        close_appointment = False

        try:
            #need to trick DOBProcessor: use a future date for date_ref
            date_ref = datetime.today() + timedelta(375)
            expected_on, variance = DOBProcessor.from_dob(self.chw.language, \
                                            expected_on_str, date_ref.date())
        except InvalidDOB:
            if expected_on_str == '000000':
                close_appointment = True
            else:
                raise BadValue(_(u"Could not understand the date of "\
                                "appointment %(expected_on)s" % \
                                {'expected_on': expected_on_str}))
        #+APT != 000000: create an next appointment
        if not close_appointment:
            if expected_on < self.date.date():
                raise BadValue(_(u"%(expected_on)s is already in the past, " \
                                "please use a future date of appointment." % \
                                    {'expected_on': expected_on}))

            aptr.appointment_date = expected_on
            aptr.status = AppointmentReport.STATUS_OPEN
            aptr.notification_sent = False
            aptr.save()
            self.response = _(u"Next appointment is on %(expected_on)s.") % \
                            {'expected_on': aptr.appointment_date}
        else:
            #+APT = 000000:no next apt child has completed the program
            self.response = _(u"No next appointment: %(patient)s has "\
                                "completed the program." % \
                                {'patient': self.encounter.patient})
        #close previous appointments
        previous_apts = AppointmentReport.objects.filter(\
                                encounter__patient=self.encounter.patient, \
                                status=AppointmentReport.STATUS_OPEN)\
                                .exclude(encounter=self.encounter)
        for apt in previous_apts:
            apt.closed_date = datetime.now()
            apt.status = AppointmentReport.STATUS_CLOSED
            apt.save()
