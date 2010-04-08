#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import re

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import VerbalAutopsyReport

class VerbalAutopsyForm(CCForm):
    KEYWORDS = {
        'en': ['va'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        va = VerbalAutopsyReport(encounter=self.encounter)
        va.done = True
        va.save()
        self.response = _("Verbal autopsy done!")
