#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Patient, Encounter
from childcount.models.reports import SPregnancy as SauriPregnancyReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField

class HouseholdForm(CCForm):
    KEYWORDS = {
        'en': ['hed','head'],
    }

    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT
    #PREVIOUS_ID = {'en': 'P'}
    MIN_HH_AGE = 10

    def process(self, patient):
   
        #Check if tokens are less than 2 at least one person shd be house hold
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected: Patient health id "\
                                "+hed | household healthid | mother health id" \
                                  "or gurdian id"))
      
        household = self.params[1]
        
        
        try:
            patient.household = Patient.objects.get( \
                                         health_id__iexact=household, \
                                         household__health_id__iexact=household)
                             
        except Patient.DoesNotExist:
            raise BadValue(_(u"Could not find head of household " \
                                  "with health ID %(id)s. You must " \
                                  "register the head of household " \
                                  "first") % \
                                  {'id': household})

        motherid = self.params[2]
        try:
            mother = Patient.objects.get(health_id__iexact=motherid, \
                                        household__health_id__iexact=household)
            if mother == patient:
                   raise BadValue(_(u"Please enter the correct information " \
                                  "u cant be your own mother "))   
                             
        except Patient.DoesNotExist:
            raise BadValue(_(u"Could not find head of mother " \
                                  "with health ID %(id)s. You must " \
                                  "register the mother first") % \
                                  {'id': household})
        
        patient.mother = mother

        patient.save()

        self.response = _("You successfuly associated  %(patient)s with " \
                            " %(father)s , %(mother)s")  %  \
                                {'patient': patient, \
                               'father':  patient.household, \
                               'mother':  patient.mother }
