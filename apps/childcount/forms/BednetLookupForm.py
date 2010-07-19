#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _
from django.db.models import Sum

from childcount.forms import CCForm
from childcount.models.reports import BedNetReport, BednetIssuedReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class BednetLookupForm(CCForm):
    KEYWORDS = {
        'en': ['bs'],
        'fr': ['bs'],
        }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #check if survey has been done
        try:
            bnr = BedNetReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except BedNetReport.DoesNotExist:
            raise ParseError(_(u"Survey Report doesnt exist for %(patient)s." \
                                " Please, contact your CHW") % \
                                {'patient': patient})
        else:
            ssite = int(bnr.sleeping_sites)
            active_bdnet = int(bnr.nets)
            bdnt_needed = ssite - active_bdnet
            #check bednet issued to date
            bdnt_issued = BednetIssuedReport.objects.filter(\
                                    encounter__patient=self.encounter.patient)\
                                    .aggregate(\
                                    stotal=Sum('bednet_received'))['stotal']
            if bdnt_issued is None:
                bdnt_issued = 0

            #calculate bednet required to be issued
            bdnt_required = bdnt_needed - bdnt_issued

            if bdnt_required <= 0:
                self.response = _(u"%(patient)s has already %(nets)d bednets" \
                                   "for %(site)d sites.") % \
                                   {'patient': patient, 'nets': bdnt_needed, \
                                    'site': bdnt_needed}

            else:
                self.response = _(u"%(patient)s need %(nets)d bednets " \
                                  "for %(site)d sites.") % \
                                    {'patient': patient, 'nets': bdnt_needed, \
                                     'site': bdnt_needed}
