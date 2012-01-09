#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import InsuranceNumberReport

from childcount.exceptions import BadValue
from childcount.exceptions import ParseError


class InsuranceNumberForm(CCForm):
    """ Insurance Number Report

    Params:
        * INSURANCE NUMBER
    """

    KEYWORDS = {
        'en': ['ins'],
        'fr': ['ins'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: Insurance Number"))

        try:
            ins_no = InsuranceNumberReport.objects.get(encounter=self.encounter)
            ins_no.reset()
        except InsuranceNumberReport.DoesNotExist:
            ins_no = InsuranceNumberReport(encounter=self.encounter)
        ins_no.form_group = self.form_group

        insurance_no = ''.join(self.params[1:])

        if len(insurance_no) <4 :
            raise BadValue(_(u"Insurance number too short."))

        ins_no.insurance_no = insurance_no
        ins_no.save()
        self.response = _(u"Insurance number: %(ins_no)s") % \
                          {'ins_no': insurance_no}

 
