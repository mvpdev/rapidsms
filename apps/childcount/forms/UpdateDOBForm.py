#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.utils import DOBProcessor
from childcount.forms import CCForm
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class UpdateDOBForm(CCForm):
    KEYWORDS = {
        'en': ['udob'],
        'fr': ['udob'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        dob = None
        lang = self.message.reporter.language

        if len(self.params) < 2:
            raise BadValue(_(u"Not enough info. Expected: New DOB."))

        dob, variance = DOBProcessor.from_age_or_dob(lang, self.params[1])

        if dob:
            patient.dob = dob
            days, weeks, months = patient.age_in_days_weeks_months()
            if days < 60 and variance > 1:
                raise BadValue(_(u"You must provide an exact birth date " \
                                      "for children under 2 months"))
            elif months < 24 and variance > 30:
                raise BadValue(_(u"You must provide an exact birth date " \
                                      "or the age in months for children " \
                                      "under two years"))

        if not dob:
            raise ParseError(_(u"Could not understand age or " \
                                    "date_of_birth of %(string)s") % \
                                    {'string': self.params[1]})

        patient.estimated_dob = variance > 1

        patient.save

        #display response
        self.response = _("You successfuly changed DOB of %(patient)s ") \
                           % {'patient': patient}
