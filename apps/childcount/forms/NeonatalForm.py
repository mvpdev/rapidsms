#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import NeonatalReport
from childcount.exceptions import ParseError, BadValue, Inapplicable


class NeonatalForm(CCForm):
    KEYWORDS = {
        'en': ['n'],
        'fr': ['n'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        days, weeks, months = patient.age_in_days_weeks_months()
        if days > 28:
            raise Inapplicable(_(u"Neonatal reports are only " \
                                  "for children less than 28 days old."))

        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: number of " \
                                "clinic visits since birth"))

        visits = self.params[1]
        if not visits.isdigit():
            raise BadValue(_("| Clinic visits since birth | must be entered " \
                             "as a number"))
        visits = int(visits)

        try:
            nr = NeonatalReport.objects.get(encounter=self.encounter)
            nr.reset()
        except NeonatalReport.DoesNotExist:
            nr = NeonatalReport(encounter=self.encounter)
        nr.form_group = self.form_group

        nr.clinic_visits = visits
        nr.save()

        if visits == 0:
            self.response = _(u"No postnatal clinic visits since birth.")
        elif visits == 1:
            self.response = _(u"One postnatal clinic visit since birth.")
        elif visits > 1:
            self.response = _(u"%(visits)d postnatal clinic visit since " \
                               "birth.") % {'visits': visits}
