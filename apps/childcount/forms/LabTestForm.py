#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from django.utils.translation import ugettext as _
from datetime import date, datetime

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import LabReport

from childcount.models import LabTest

from childcount.exceptions import BadValue
from childcount.exceptions import ParseError

import random


class LabTestForm(CCForm):
    """ LAB TEST Report

    Params:
        * LAB TEST REQUESTED
    """

    KEYWORDS = {
        'en': ['q'],
        'rw': ['q'],
        'fr': ['q'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info.Expected: LAB Test Requested"))

        try:
            labtest = LabReport.objects.get(encounter=self.encounter)
            labtest.reset()
        except LabReport.DoesNotExist:
            labtest = LabReport(encounter=self.encounter)
        labtest.form_group = self.form_group

        test_requested = ''.join(self.params[1])

        try:
            test_obj = LabTest.objects.get(code=test_requested)
        except LabReport.DoesNotExist:
            raise ParseError(_(u"Unknown Lab Request (%s) Try again") \
                                %test_requested)
    
        labtest.lab_test = test_obj

        #SAMPLE NUMBER YEAR-CLINICCODE-NUMBER
        now = datetime.now()      
        if self.chw.clinic:
            clinic_code = self.chw.clinic.code
            year_month = now.strftime("%y%m")
            
            search_pattern = "WAT-1202" clinic_code+"-"+year_month
            
            #search no of samples that exist
            print "Search for lab for this month %s " % search_pattern

            result = LabReport.objects.filter(sample_no__istartswith=search_pattern)
            counter = result.count()
            if counter > 0:
                counter = counter+1
                last_item = result.latest().sample_no
                p = last_item.replace(search_pattern+"-","")
                if int(counter) <= int(p):
                    counter = p+1
                    counter = "%03d" % counter
                    lab_sample_no = search_pattern+"-"+counter
                else:
                    counter = "%03d" % counter
                    lab_sample_no = search_pattern+"-"+counter                    
            else:
                counter = "%03d" % 1
                lab_sample_no = search_pattern+"-"+counter

        else:
            raise ParseError(_(u"Youre not assigned clinic, consult admin"))
        
        labtest.sample_no = lab_sample_no

        labtest.save()

        self.response = _(u"Sample Number: %(lab_no)s") % \
                          {'lab_no': lab_sample_no}

