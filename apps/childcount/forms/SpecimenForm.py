#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import SpecimenReport

from childcount.exceptions import BadValue
from childcount.exceptions import ParseError


class SpecimenForm(CCForm):
    """Specimen Report  Form

    Params:
        * Number of Blood tubes
        * Sputum Sample 
        * Stool Sample 
        * Urine Sample
    """

    KEYWORDS = {
        'en': ['sp'],
        'fr': ['sp'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        expected = _(u"| Number of Blood tubes | Sputum Sample |  " \
                      "Stool Sample | Urine Sample |")

        if len(self.params) < 5:
            raise ParseError(_(u"Not enough info.Expected: " \
                                "%(expected)s") % {'expected': expected})

        try:
            sp = SpecimenReport.objects.get(encounter=self.encounter)
            sp.reset()
        except SpecimenReport.DoesNotExist:
            sp = SpecimenReport(encounter=self.encounter)
        sp.form_group = self.form_group
  
        #NUmber of Blood Tubes
        if not self.params[1].isdigit():
            raise ParseError(_(u"Number of Blood Tubes must be a " \
                                "number"))

        sp.blood_tubes = int(self.params[1])

        #NUmber of Sputum Sample
        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of Sputum sample must be a " \
                                "number"))

        sp.sputum_sample = int(self.params[2])

        #NUmber of Stool Sample
        if not self.params[3].isdigit():
            raise ParseError(_(u"Number of Stool sample must be a " \
                                "number"))

        sp.stool_sample = int(self.params[3])

        #NUmber of Urine Sample
        if not self.params[4].isdigit():
            raise ParseError(_(u"Urine Sample must be a " \
                                "number"))

        sp.urine_sample = int(self.params[4])

        sp.save()

        message = '';
        '''
        if sp.blood_tubes > 0:
            message += _(u"%(codes)s Blood Tubes,") % \
                             {'codes': sp.blood_tubes}
        if sp.sp.sputum_sample > 0:
            message += _(u" Sputum Sample %(codes)s ") % \
                             {'codes': sp.sputum_sample}

        if sp.stool_sample > 0:
            message += _(u"Stool sample ")

        if sp.urine_sample > 0:
            message += _(u"Urine Sample ")
        '''
        self.response = _(u"Specimen Saved:  %s") % message

