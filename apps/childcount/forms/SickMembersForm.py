#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import SickMembersReport
from childcount.models import Encounter
from childcount.exceptions import ParseError


class SickMembersForm(CCForm):
    KEYWORDS = {
        'en': ['e'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):

        try:
            smr = SickMembersReport.objects.get(encounter=self.encounter)
        except SickMembersReport.DoesNotExist:
            smr = SickMembersReport(encounter=self.encounter)
        smr.form_group = self.form_group

        if len(self.params) < 5:
            raise ParseError(_(u"Not enough info, expected: number of sick " \
                                "| number of RDTs | number of positive RDTs " \
                                "| number on treatment"))

        sick = self.params[1]
        if not sick.isdigit():
            raise ParseError(_(u"Number of sick must be a number"))
        smr.sick = int(sick)

        rdts = self.params[2]
        if not rdts.isdigit():
            raise ParseError(_(u"Number of RDTs must be a number"))
        smr.rdts = int(rdts)

        positive_rdts = self.params[3]
        if not positive_rdts.isdigit():
            raise ParseError(_(u"Number of positive RDTs must be a number"))
        smr.positive_rdts = int(positive_rdts)

        on_treatment = self.params[4]
        if not on_treatment.isdigit():
            raise ParseError(_(u"Number of other people on treatment " \
                                "must be a number"))
        smr.on_treatment = int(on_treatment)

        smr.save()

        self.response = smr.summary()
