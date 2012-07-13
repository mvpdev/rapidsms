#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import ExtendedBedNetReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable

class ExtendedBednetCoverageForm(CCForm):
    """ BednetCoverageForm

    Params:
        * Number of people(int)
        * Sleeping sites(int)
        * Earlier Bednets(int)
        * Function Bednets(int)
        * Damaged Bednets(int)
    """

    KEYWORDS = {
        'en': ['ebc'],
        'rw': ['ebc'],
        'fr': ['bce'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 6:
            raise ParseError(_(u"Not enough info. Expected: | number of people | "\
                                "number of sleeping" \
                                " sites | number of functioning bednets |" \
                                " earlier bednet | damaged bednet |"))

        try:
            bnr = ExtendedBedNetReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except ExtendedBedNetReport.DoesNotExist:
            bnr = ExtendedBedNetReport(encounter=self.encounter)
            overwrite = False
        else:
            bnr.reset()
            overwrite = True

        bnr.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of people must be " \
                                "a number."))

        bnr.people = int(self.params[1])
        if bnr.people < 0:
            raise ValueError(_("| Number of people cannot be negative."))

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of sleeping sites must be " \
                                "a number."))

        bnr.sleeping_sites = int(self.params[2])
        if bnr.sleeping_sites < 0:
            raise ValueError(_("| Number of sleeping sites cannot be negative."))

        if not self.params[3].isdigit():
            raise ParseError(_(u"| Number of bednets received earlier " \
                                "must be a number."))

        bnr.earlier_nets = int(self.params[3])
        if bnr.earlier_nets < 0:
            raise ValueError(_("| Number of nets given earlier cannot be negative."))

        if not self.params[4].isdigit():
            raise ParseError(_(u"| Number of available " \
                                "bednets must be a number."))

        bnr.function_nets = int(self.params[4])
        if bnr.function_nets < 0:
            raise ValueError(_("| Number of functioning nets cannot be negative."))

        if not self.params[5].isdigit():
            raise ParseError(_(u"| Number of damaged bednets received " \
                                "must be a  number."))

        bnr.damaged_nets = int(self.params[5])
        if bnr.damaged_nets < 0:
            raise ValueError(_("| Number of damage nets cannot be negative.")) 
        bnr.save()

        self.response = _(u"%(patient)s: %(p)d people, "\
                            "%(sites)d sleeping site(s), " \
                            "%(er)d net(s) given earlier, "\
                           "%(nets)d net(s) available, "\
                           "%(dm)d damaged net(s).") % \
                           {'patient': patient, 'sites': bnr.sleeping_sites, \
                            'nets': bnr.function_nets, \
                            'er': bnr.earlier_nets, 'dm': bnr.damaged_nets,
                            'p':bnr.people}
