#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import BednetUtilization
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class BednetUtilizationForm(CCForm):
    """ Bednet Utilization

    Params:
        * number of children who slept here last night
        * Children slept under bednet (int)
    """

    KEYWORDS = {
        'en': ['bu'],
        'rw': ['bu'],
        'fr': ['bu'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: | number of " \
                                "children who slept here last night | "\
                                " how many slept under bednets "))

        try:
            bnut_rpt = BednetUtilization.objects.get(encounter=self.encounter)
            bnut_rpt.reset()
        except BednetUtilization.DoesNotExist:
            bnut_rpt = BednetUtilization(encounter=self.encounter)
            overwrite = False

        bnut_rpt.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of children who slept here last" \
                                " night | should be a number."))

        bnut_rpt.child_underfive = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of children under bednet | should " \
                                "be a number."))

        bnut_rpt.child_lastnite = int(self.params[2])

        if bnut_rpt.child_lastnite > bnut_rpt.child_underfive:
            raise ParseError(_(u"Number of under five who slept here last " \
                                "night should be more than those who slept " \
                                "under bednet"))


        self.response = _(u"%(sites)d child(ren) slept here last night. " \
                           "%(nets)d slept under bednet(s). ") % \
                           {'sites': bnut_rpt.child_underfive, \
                            'nets': bnut_rpt.child_lastnite }

        bnut_rpt.save()
