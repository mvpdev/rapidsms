#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _
from django.db.models import Sum

from childcount.forms import CCForm
from childcount.models.reports import BedNetReport, BednetIssuedReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class BednetDistributionForm(CCForm):
    KEYWORDS = {
        'en': ['bnd'],
        'fr': ['bnd'],
        }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #check if house hold survey has been taken
        try:
            bnr = BedNetReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except BedNetReport.DoesNotExist:
            raise ParseError(_(u"Report  Survey doesnt exist for " \
                                "%(patient)s ") % {'patient': patient})
        else:
            ssite = bnr.sleeping_sites
            active_bdnet = bnr.nets
            bdnt_needed = ssite - active_bdnet

        #create object
        try:
            pr = BednetIssuedReport.objects.get(encounter=self.encounter)
            pr.reset()
        except BednetIssuedReport.DoesNotExist:
            pr = BednetIssuedReport(encounter=self.encounter)

        pr.form_group = self.form_group

        #check bednet issued to date
        bdnt_issued = BednetIssuedReport.objects.filter(\
                                    encounter__patient=self.encounter.patient)\
                                    .aggregate(\
                                    stotal=Sum('bednet_received'))['stotal']
        if bdnt_issued is None:
            bdnt_issued = 0

        #calculate bednet required to be issued
        bdnt_required = bdnt_needed - bdnt_issued
        #if less then zero nno bed ned required
        if bdnt_required < 0:
            self.response = _(u"%(patient)s .Has already received %(nets)d " \
                               "for sleeping %(site)d sites.  ") % \
                               {'patient': patient, 'nets': bdnt_needed, \
                                'site': bdnt_needed}
        else:
            self.response = _(u"%(patient)s. %(ssite)d Sleeping sites.Need " \
                               "%(bdnt_required)d bednet(s).Last " \
                               "received: ") % \
                               {'patient': patient, 'ssite': bdnt_needed, \
                                'bdnt_required': bdnt_required}

        pr.bednet_received = bdnt_required
        pr.save()
