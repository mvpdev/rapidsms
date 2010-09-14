#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import BedNetReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class BednetCoverageForm(CCForm):
    KEYWORDS = {
        'en': ['bc'],
        'fr': ['bc'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 5:
            raise ParseError(_(u"Not enough info. Expected: | sleeping" \
                                " sites | number of functioning bednets |" \
                                " earlier bednet | damaged bednet |"))

        try:
            bnr = BedNetReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except BedNetReport.DoesNotExist:
            bnr = BedNetReport(encounter=self.encounter)
            overwrite = False
        else:
            bnr.reset()
            overwrite = True

        bnr.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of sleeping sites | must be " \
                                "a number."))

        bnr.sleeping_sites = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of functioning (recent received)" \
                                " bednet | must be a number."))

        bnr.function_nets = int(self.params[2])
        bnr.function_nets
        if not self.params[3].isdigit():
            raise ParseError(_(u"| Number of bednets received earlier | " \
                                "must be a number."))

        bnr.earlier_nets = int(self.params[3])

        if not self.params[4].isdigit():
            raise ParseError(_(u"| Number of damaged bednets received | " \
                                "recent must be a  number."))

        bnr.damaged_nets = int(self.params[4])
        bnr.save()

        self.response = _(u"%(patient)s: %(sites)d sleeping site(s), " \
                           "%(nets)d bednet(s). Earlier: %(er)d. " \
                           "Damaged bednet: %(dm)d.") % \
                           {'patient': patient, 'sites': bnr.sleeping_sites, \
                            'nets': bnr.function_nets, \
                            'er': bnr.earlier_nets, 'dm': bnr.damaged_nets}
