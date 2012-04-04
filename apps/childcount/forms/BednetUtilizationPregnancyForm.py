#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import BednetUtilizationPregnancy
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class BednetUtilizationPregnancyForm(CCForm):
    """ 
    Bednet Utilization Pregnancy

    Params:
        * # pregnant women who slept here last night
        * # pregnant women slept under bednet (int)
    """

    KEYWORDS = {
        'en': ['bp'],
        'rw': ['bp'],
        'fr': ['bp'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: | number of " \
                                "pregnant women who slept here last night | "\
                                " how many slept under bednets "))

        try:
            bnut_rpt = BednetUtilizationPregnancy.objects.get(encounter=self.encounter)
            bnut_rpt.reset()
        except BednetUtilizationPregnancy.DoesNotExist:
            bnut_rpt = BednetUtilizationPregnancy(encounter=self.encounter)
            overwrite = False

        bnut_rpt.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of pregnant women whoslept here" \
                                " last night should be a number."))

        bnut_rpt.slept_lastnite = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of pregnant women who slept  " \
                                "under bednet should be a number."))

        bnut_rpt.slept_underbednet = int(self.params[2])

        if bnut_rpt.slept_underbednet > bnut_rpt.slept_lastnite:
            raise ParseError(_(u"Number of pregnant women who slept" \
                                "here last  night should be more than those" \
                                " who slept under bednet"))


        self.response = _(u"%(sites)d pregnant women slept here last night. " \
                           "%(nets)d slept under bednet(s). ") % \
                           {'sites': bnut_rpt.slept_lastnite, \
                            'nets': bnut_rpt.slept_underbednet }

        bnut_rpt.save()
