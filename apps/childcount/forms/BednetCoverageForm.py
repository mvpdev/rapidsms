#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import BedNetReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class BednetCoverageForm(CCForm):
    """ 
    BednetCoverageForm
    Params:
        * Sleeping sites(int)
        * Function Bednets(int)
        * Functioning Bednets Observed(int)
    """

    KEYWORDS = {
        'en': ['bc'],
        'rw': ['bc'],
        'fr': ['bc'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 4:
            raise ParseError(_(u"Not enough info. Expected: | sleeping" \
                                " sites | number of functioning bednets |" \
                                "number of functioning bednets  observed."))

        try:
            bnr = BedNetReport.objects.get(encounter=self.encounter)
            bnr.reset()
        except BedNetReport.DoesNotExist:
            bnr = BedNetReport(encounter=self.encounter)
            overwrite = False

        bnr.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of sleeping sites | must be " \
                                "a number."))

        bnr.sleeping_sites = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of functioning bednet | must be" \
                                " a number."))

        bnr.function_nets = int(self.params[2])
        
        if not self.params[3].isdigit():
            raise ParseError(_(u"| Number of functioning bednet observed | " \
                                "must be a number."))

        bnr.function_nets_observed = int(self.params[3])

        bnr.save()

        self.response = _(u"%(patient)s: %(sites)d sleeping site(s), " \
                           "%(nets)d functioning bednet(s).  %(er)d. " \
                           "observed") % \
                           {'patient': patient, 'sites': bnr.sleeping_sites, \
                            'nets': bnr.function_nets, \
                            'er': function_nets_observed}
