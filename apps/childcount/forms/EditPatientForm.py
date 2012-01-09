#!/usr/bin/env python
# -*- coding: utf-8 -*-
# maintainer: alou

from django.utils.translation import ugettext as _

from childcount.exceptions import ParseError
from childcount.forms import CCForm
from childcount.models import Encounter

class EditPatientForm(CCForm):
    """ Change First and Last Name of a Patient

    Params:
        * first_name
        * last_name
    """

    KEYWORDS = {
        'en': ['edit'],
        'rw': ['edit'],
        'fr': ['edit', 'mod'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        if self.params.__len__() < 3:
            raise ParseError(_(u"Not enough info. Expected: " \
                                "| First Name | Last Name |"))

        first_name = self.params[1]
        last_name = self.params[2]

        patient.first_name = first_name
        patient.last_name = last_name
        patient.save()

        self.response += _(u"Updated Patient info: %(patient)s" \
                         % {'patient': patient})
