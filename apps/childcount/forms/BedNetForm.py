#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import BedNetReport
from childcount.exceptions import ParseError


class BedNetForm(CCForm):
    KEYWORDS = {
        'en': ['bn'],
        'fr': ['bn'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: number of " \
                                "sleeping sites and number of bednets."))

        try:
            bnr = BedNetReport.objects.get(encounter=self.encounter)
            bnr.reset()
        except BedNetReport.DoesNotExist:
            bnr = BedNetReport(encounter=self.encounter)
        bnr.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"Number of sleeping sites must be entered as" \
                                " a number."))

        bnr.sleeping_sites = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of bednets must be a " \
                                "number"))

        bnr.nets = int(self.params[2])

        bnr.save()

        self.response = _(u"%(sites)d sleeping site(s), %(nets)d bednet(s)") %\
                           {'sites': bnr.sleeping_sites, 'nets': bnr.nets}
