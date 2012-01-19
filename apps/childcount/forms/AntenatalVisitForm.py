#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga


from datetime import datetime, timedelta, time
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Configuration
from childcount.models.reports import AntenatalVisitReport
from childcount.models import Encounter
from childcount.exceptions import ParseError, BadValue, InvalidDOB
from childcount.utils import DOBProcessor

from alerts.utils import SmsAlert


class AntenatalVisitForm(CCForm):
    """ Antenatal Visit

    Params:
        * date of Antenatal Visit
    """

    KEYWORDS = {
        'en': ['pf'],
        'rw': ['pf'],
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
        reminder_date = expected_on - timedelta(weeks=3)
        if reminder_date < self.date.date():
            msg = _(u"Please send %(patient)s to the health center if  " \
                "they have not visited the clinic in the last 2 weeks.") % \
                {'patient': patient}
            send_at = None
        else:
            msg = _(u"Please send %(patient)s to the health center for " \
                "their appointment") % \
                {'patient': patient}
            send_at = datetime.combine(reminder_date, time(7, 0))
        alert = SmsAlert(reporter=self.chw, msg=msg)
        sms_alert = alert.send(send_at=send_at)
        sms_alert.name = u"three_weeks_before_delivery"
        sms_alert.save()
        avr.sms_alert = sms_alert
        avr.save()
