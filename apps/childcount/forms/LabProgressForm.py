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

from childcount.forms.utils import MultipleChoiceField


class LabProgressForm(CCForm):
    """ LAB Rquisition Progress Form

    """

    KEYWORDS = {
        'en': ['qp'],
        'rw': ['qp'],
        'fr': ['qp'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        progress_field = MultipleChoiceField()
        progress_field.add_choice('en', LabReport.PRO_RECEIVED, 'R')
        progress_field.add_choice('en', LabReport.PRO_INSUFFICIENT, 'IQ')
        progress_field.add_choice('en', LabReport.PRO_BADQUALITY, 'BQ')
        progress_field.add_choice('en', LabReport.PRO_WRONGTYPE, 'WT')
        progress_field.add_choice('en', LabReport.PRO_NOSAMPLE, 'NS')

        progress_field.add_choice('rw', LabReport.PRO_RECEIVED, 'R')
        progress_field.add_choice('rw', LabReport.PRO_INSUFFICIENT, 'IQ')
        progress_field.add_choice('rw', LabReport.PRO_BADQUALITY, 'BQ')
        progress_field.add_choice('rw', LabReport.PRO_WRONGTYPE, 'WT')
        progress_field.add_choice('rw', LabReport.PRO_NOSAMPLE, 'NS')

        progress_field.add_choice('fr', LabReport.PRO_RECEIVED, 'R')
        progress_field.add_choice('fr', LabReport.PRO_INSUFFICIENT, 'IQ')
        progress_field.add_choice('fr', LabReport.PRO_BADQUALITY, 'BQ')
        progress_field.add_choice('fr', LabReport.PRO_WRONGTYPE, 'WT')
        progress_field.add_choice('fr', LabReport.PRO_NOSAMPLE, 'NS')

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info.Expected: LAB Results "\
                                "Requested"))

        ''' 
        GET ANY OPEN, LAB REPORT
        USE SAMPLE NUMBER AS IDENTIFIER
        '''
        sample_no = self.params[1]

        try:
            labtest = LabReport.objects.get(sample_no=sample_no)
        except LabReport.DoesNotExist:
            raise ParseError(_(u"Unknown LabTest Request (%s) Check " \
                                "Sampleno and try again")  %sample_no )


        progress_field.set_language(self.chw.language)

        #Get Progress STATUS
        req_code = self.params[2]
        if not progress_field.is_valid_choice(req_code):
            raise ParseError(_(u"| Req. Progress code should be %(choices)s.") \
                             % {'choices': progress_field.choices_string()})

        labtest.progress_status = progress_field.get_db_value(req_code)

        if labtest.progress_status == LabReport.PRO_RECEIVED:
            labtest.status = LabReport.STATUS_INPROGRESS
        if labtest.progress_status  == LabReport.PRO_NOSAMPLE:
            labtest.status = LabReport.STATUS_STALLED
        if labtest.progress_status  == LabReport.PRO_INSUFFICIENT:
            labtest.status = LabReport.STATUS_STALLED
        if labtest.progress_status  == LabReport.PRO_WRONGTYPE:
            labtest.status = LabReport.STATUS_STALLED
        if labtest.progress_status  == LabReport.PRO_BADQUALITY:
            labtest.status = LabReport.STATUS_STALLED

        labtest.save()

        self.response = _(u"Requisition Progress: %(req_code)s") % \
                          {'req_code': labtest.get_progress_status_display()}

