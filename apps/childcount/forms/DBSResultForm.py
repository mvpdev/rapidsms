#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import re
import calendar
from datetime import datetime
from datetime import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.models import Patient, Encounter
from childcount.models.reports import DBSResultReport
from childcount.models.reports import AppointmentReport
from childcount.forms.utils import MultipleChoiceField


class DBSResultForm(CCForm):
    KEYWORDS = {
        'en': ['dr'],
        'fr': ['dr'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        try:
            dbsr = DBSResultReport.objects.get(encounter=self.encounter)
        except DBSResultReport.DoesNotExist:
            dbsr = DBSResultReport(encounter=self.encounter)
            overwrite = False
        else:
            dbsr.reset()
            overwrite = True
        dbsr.form_group = self.form_group

        dbsr.returned = True
        dbsr.save()
        self.response = _(u"Results received")
        #an appointment in 3/4 days from today
        try:
            aptr = AppointmentReport.objects.get(encounter=self.encounter)
        except AppointmentReport.DoesNotExist:
            aptr = AppointmentReport(encounter=self.encounter)
            overwrite = False
        else:
            aptr.reset()
            overwrite = True
        #alert should happen tomorrow morning hence 4 days
        delay = datetime.today() + relativedelta(days=4, hours=7)
        if delay.weekday() > calendar.FRIDAY:
            delay = datetime.today() + relativedelta(weekday=calendar.MONDAY)
        aptr.appointment_date = delay
        aptr.status = AppointmentReport.STATUS_OPEN
        aptr.notification_sent = False
        aptr.save()
