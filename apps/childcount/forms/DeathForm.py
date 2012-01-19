#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import time
from datetime import date, datetime, timedelta

from django.utils.translation import ugettext as _

from bonjour import dates

from childcount.forms import CCForm
from childcount.exceptions import BadValue, ParseError, InvalidDOB
from childcount.exceptions import Inapplicable
from childcount.models import Configuration
from childcount.models.reports import DeathReport, PregnancyReport
from childcount.models import Patient, Encounter
from childcount.utils import DOBProcessor, alert_health_team

from reporters.models import Reporter

from alerts.utils import SmsAlert

class DeathForm(CCForm):
    """ Register a death

    Params:
        * date of death
    """

    KEYWORDS = {
        'en': ['dda'],
        'rw': ['dda'],
        'fr': ['dda'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: date of death."))

        try:
            dr = DeathReport.objects.get(encounter=self.encounter)
        except DeathReport.DoesNotExist:
            dr = DeathReport(encounter=self.encounter)
            overwrite = False
        else:
            dr.reset()
            overwrite = True
        dr.form_group = self.form_group

        if DeathReport.objects.filter(encounter__patient=patient).count() > 0:
            dr = DeathReport.objects.filter(encounter__patient=patient)[0]
            raise Inapplicable(_(u"A death report for %(p)s was already " \
                                  "submited by %(chw)s.") % \
                                  {'p': patient, 'chw': dr.chw()})

        dod_str = ' '.join(self.params[1:])
        try:
            dod, variance = DOBProcessor.from_dob(self.chw.language, dod_str, \
                                                  self.date.date())
        except InvalidDOB:
            raise BadValue(_(u"Could not understand date of death: " \
                             "%(dod)s.") % \
                             {'dod': dod_str})

        dr.death_date = dod
        dr.save()

        msg = _("Died on %(dod)s.") % {'dod': dod}

        if patient.is_head_of_household():
            hh = Patient.objects\
                .filter(household__pk=patient.pk)\
                .exclude(pk=patient.pk)\
                .order_by('dob')

            new_head = hh[0]
            n = hh.update(household=new_head)

            msg += _(" Changed head of household for %(n)d family " \
                    "member(s) to %(hid)s (%(hh)s)") % \
                {'hh': new_head.full_name(), \
                'hid':new_head.health_id.upper(),
                'n': n}

        patient.status = Patient.STATUS_DEAD
        patient.save()

        self.response = msg

        # If patient is in priority group, send alert about death
        # to HC Staff and Health Team
        print "$$$$$$%s" % self._is_alert_eligible(dr)
        if self._is_alert_eligible(dr):
            self._send_alert(dr)


    def _is_alert_eligible(self, drep): 
        """Check if patient is in priority group (under age 5 or 
        pregnant within the past 42 days) 
        """ 

        patient = drep.encounter.patient

        # Patient is an Under-Five
        if patient.years() < 5: 
            return True

        # Patient was pregnant in last 42 days
        if Patient\
                .objects\
                .filter(pk=patient.pk)\
                .pregnant_recently(datetime.now() - timedelta(30), datetime.now())\
                .count() > 0:
            return True

        return False

    def _send_alert(self, drep):
        msg = _("Patient %(patient)s "\
                "from %(loc)s (%(loc_code)s) died on %(dod)s. " \
                "Contact CHW %(chw)s for more information.") % \
                    {'patient': drep.encounter.patient,
                     'loc': drep.encounter.patient.location.name,
                     'loc_code': drep.encounter.patient.location.code.upper(),
                     'dod': dates.format_date(drep.death_date, 'short'),
                     'chw': drep.encounter.patient.chw}

        alert_health_team("death_alert", msg)

