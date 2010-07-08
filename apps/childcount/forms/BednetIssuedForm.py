#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _
from django.db.models import Sum

from childcount.forms import CCForm
from childcount.models.reports import BedNetReport, BednetIssuedReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class BednetIssuedForm(CCForm):
    KEYWORDS = {
        'en': ['bd'],
        'fr': ['bd'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #check if house hold survey has been taken
        try:
            bnr = BedNetReport.objects.get(\
                    encounter__patient=self.encounter.patient)
        except BedNetReport.DoesNotExist:
            raise ParseError(_(u"Survey Report doesnt exist for %(pat)s") % \
                                {'pat': patient})
        else:
            ssite = bnr.sleeping_sites
            active_bdnet = bnr.nets
            bdnt_needed = ssite - active_bdnet

        #Check earlier report and modify
        try:
            pr = BednetIssuedReport.objects.filter(\
                                    encounter__patient=self.encounter.patient)\
                                    .latest()
        except BednetIssuedReport.DoesNotExist:
            pr = BednetIssuedReport(encounter=self.encounter)

        pr.form_group = self.form_group

        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: number of " \
                                " bednets issued."))
        if not self.params[1].isdigit():
            raise ParseError(_(u"Bednet issued should be number"))
        bdnt = self.params[1]

        self.response = _(u"%(patient)s. Has received %(bdnt)s bednet") % \
                                    {'patient': patient, 'bdnt': bdnt}

        pr.bednet_received = bdnt
        pr.save()
