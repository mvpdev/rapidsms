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
from childcount.models.reports import CD4ResultReport


class CD4ResultForm(CCForm):
    """ CD4 Result

    Params:
        * CD4 Value (range 0-999)
    """

    KEYWORDS = {
        'en': ['cd'],
        'rw': ['cd'],
        'fr': ['cd'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: | CD4 Value | " \
                            "must be in range 0-999"))
        if not self.params[1].isdigit():
            raise BadValue(_(u"Bad value %(value)s. Expected: | CD4 Value | " \
                            "must be a number in range 0-999") % \
                            {'value': self.params[1]})
        if int(self.params[1]) not in range(0, 1000):
            raise BadValue(_(u"Bad value %(value)s. Expected: | CD4 Value | " \
                            "must be in range 0-999") % \
                            {'value': self.params[1]})
        try:
            cdr = CD4ResultReport.objects.get(encounter=self.encounter)
        except CD4ResultReport.DoesNotExist:
            cdr = CD4ResultReport(encounter=self.encounter)
            overwrite = False
        else:
            cdr.reset()
            overwrite = True
        cdr.form_group = self.form_group

        cdr.cd4_count = int(self.params[1])
        cdr.save()
        self.response = _(u"CD4 Count Results received (%(count)s)") % \
                            {'count': cdr.cd4_count}
