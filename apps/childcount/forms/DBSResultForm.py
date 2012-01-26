#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
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
    """ DBS Result

    Params:
        * Positive (y/n)
    """

    KEYWORDS = {
        'en': ['db'],
        'rw': ['db'],
        'fr': ['db'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        result_field = MultipleChoiceField()
        result_field.add_choice('en', \
                            DBSResultReport.RESULT_POSITIVE, 'Y')
        result_field.add_choice('en', \
                            DBSResultReport.RESULT_NEGATIVE, 'N')
        result_field.add_choice('rw', \
                            DBSResultReport.RESULT_POSITIVE, 'Y')
        result_field.add_choice('rw', \
                            DBSResultReport.RESULT_NEGATIVE, 'N')
        result_field.add_choice('fr', \
                            DBSResultReport.RESULT_POSITIVE, 'O')
        result_field.add_choice('fr', \
                            DBSResultReport.RESULT_NEGATIVE, 'N')
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: | Positive | " \
                            "must be %(choices)s.") % \
                              {'choices': result_field.choices_string()})
        result_field.set_language(self.chw.language)
        if not result_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"| Positive | must be %(choices)s.") % \
                              {'choices': result_field.choices_string()})
        test_result = result_field.get_db_value(self.params[1])
        try:
            dbsr = DBSResultReport.objects.get(encounter=self.encounter)
        except DBSResultReport.DoesNotExist:
            dbsr = DBSResultReport(encounter=self.encounter)
            overwrite = False
        else:
            dbsr.reset()
            overwrite = True
        dbsr.form_group = self.form_group

        dbsr.test_result = test_result
        dbsr.save()
        #save current hiv status for the patient
        patient.hiv_status = test_result
        patient.save()
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
        #alert should happen morning hence 4 days
        delay = datetime.today() + relativedelta(days=4, hours=7)
        if delay.weekday() > calendar.FRIDAY:
            delay = datetime.today() + relativedelta(weekday=calendar.MONDAY)
        aptr.appointment_date = delay
        aptr.status = AppointmentReport.STATUS_OPEN
        aptr.save()
