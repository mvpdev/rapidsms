#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

import re
import time
from datetime import date

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import BadValue, ParseError, InvalidDOB
from childcount.exceptions import Inapplicable

from childcount.models import Patient, Encounter
from childcount.models.reports import PatientStatusReport
from childcount.forms.utils import MultipleChoiceField


class InactivatePatientForm(CCForm):
    """ Patient set status

    Params:
        * status (Y/N)
    """

    KEYWORDS = {
        'en': ['active'],
        'rw': ['active'],
        'fr': ['active'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: Patient status: " \
                                u"activate(Y) deactivate (N)"))

        status_field = MultipleChoiceField()
        status_field.add_choice('en', PatientStatusReport.STATUS_ACTIVE, 'Y')
        status_field.add_choice('en', PatientStatusReport.STATUS_INACTIVE, 'N')
        status_field.add_choice('rw', PatientStatusReport.STATUS_ACTIVE, 'Y')
        status_field.add_choice('rw', PatientStatusReport.STATUS_INACTIVE, 'N')
        status_field.add_choice('fr', PatientStatusReport.STATUS_ACTIVE, 'O')
        status_field.add_choice('fr', PatientStatusReport.STATUS_INACTIVE, 'N')
        try:
            psr = PatientStatusReport.objects.get(encounter=self.encounter)
        except PatientStatusReport.DoesNotExist:
            psr = PatientStatusReport(encounter=self.encounter)
            overwrite = False
        else:
            psr.reset()
            overwrite = True

        psr.form_group = self.form_group
        status_field.set_language(self.chw.language)

        status = self.params[1]
        if not status_field.is_valid_choice(status):
            raise ParseError(_(u"| Status : ? | "\
                                "must be %(choices)s.") \
                             % {'choices': status_field.choices_string()})
        psr.status = status_field.get_db_value(status)

        if len(self.params) > 2:
            psr.reason = ' '.join(self.params[3:])

        #apply patient status to relocated and save
        patient.status = status_field.get_db_value(status)
        patient.save()

        psr.save()

        self.response = _("%(patient)s status updated") % \
                           {'patient': patient}
