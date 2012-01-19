#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from datetime import datetime, date

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Text, Section

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

from childcount.indicators import birth
from childcount.indicators import death

from childcount.models import Patient
from childcount.models.reports import ( MedicineGivenReport,
                                   NutritionReport,FeverReport)


def textify_list(cells):
    """ returns list of Text() from list """
    first = True
    nl = []
    for cell in cells:
        if first:
            elem = Text(cell, size=7, bold=True)
            first = False
        else:
            elem = Text(cell)
        nl.append(elem)
    return nl

def date_under_five(end_date):
    """ Returns the date reduced by five years  from enddate of report"""
    today = end_date
    date_under_five = date(today.year - 5, today.month, today.day)
    return date_under_five

def date_under_one(end_date):
    """ Returns the date reduced by ONE years  from Period enddate """
    today = end_date
    date_under_one= date(today.year - 1, today.month, today.day)
    return date_under_one

class ReportDefinition(PrintedReport):
    title = _(u"Medicine Given Report ")
    filename = 'Medicine_given_report_'
    formats = ['pdf','html', 'xls']
    variants = []

    def generate(self, time_period, rformat, title, filepath, data):
        
        doc = Document(title, landscape=True)

        self.period = time_period

        self.set_progress(0)

        # Get Sub_Periods
        sub_periods = time_period.sub_periods()
        
        #
        header_row = [Text(_(u'Indicator'))]

        for sub_period in time_period.sub_periods():
            header_row.append(Text(sub_period.title))

        self.table = Table(header_row.__len__(), \
                     Text(_("Medicine Given Report: %s") % time_period.title))
        
        self.table.add_header_row(header_row)

        self.set_progress(10)

        # first column is left aligned
        self.table.set_alignment(Table.ALIGN_LEFT, column=0)
        # first column has width of 20%
        self.table.set_column_width(13, column=0)

        #Number of RDT+
        self._add_number_rdt(FeverReport, _(u"Number of RDT+"))

        #Number of Cortem given
        self._add_number_cortem(MedicineGivenReport, _(u"Number of Cortem given"))

        #Number of ORS given
        self._add_number_ors(MedicineGivenReport, _(u"Number of ORS given"))

        #Number of ZINC given
        self._add_number_zinc(MedicineGivenReport, _(u"Number of Zinc given"))

        #Number of Under-5 children screened with MUACs
        self._add_underfive_muac(NutritionReport, \
                          _(u"Number of Under-5 children screened with MUACs"))

        #Number of those U5 screened who have reading of 120 and + mm
        self._add_underfive_muac_maln(NutritionReport, _(u"Number of those U5 "  \
                                "screened who have reading of 120 and + mm"))

        self.set_progress(40)
        #Number of those U5 screened who have reading of 
        #less than 120 but more than 115mm
        self._add_underfive_muac_mid(NutritionReport, _(u"Number of those U5 "\
                                    "screened who have reading ofless than " \
                                    "120 but more than 115mm"))

        #Number of those U5 screened who have reading of less than 115mm
        self._add_underfive_muac_small(NutritionReport, _(u"Number of those U5 "\
                                "screened who have reading of less than 115mm"))

        #Number of Under-1 children screened with MUACs
        self._add_underone_muac(NutritionReport, _(u"Number of Under-1 "\
                                    "children screened with MUACs"))

        #Number of those U1 screened who have reading of 120 and + mm
        self._add_underone_muac_maln(NutritionReport, _(u"Number of those U1 "\
                                   "screened who have reading of 120 and + mm"))

        #NNumber of those U1 screened who have reading 
        #of less than 120 but more than 115mm
        self._add_underone_muac_mid(NutritionReport, _(u"Number of those U1 "\
                                   "screened who have reading of 120 and + mm"))


        #Number of those U1 screened who have reading of less than 115mmrow)
        self._add_underone_muac_small(NutritionReport, _(u"Number of those U1 "\
                        "screened who have reading of less than 115mmrow)"))


        doc.add_element(self.table)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval


    def _add_number_rdt(self, name='', line=''):

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            month = name\
                .objects\
                .filter(encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)


    def _add_number_cortem(self, name='', line=''):
        """ Number of Cortem """

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            month = name\
                .objects\
                .filter(encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

    def _add_number_ors(self, name='', line=''):
        """ Number of ORS """

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            month = name\
                .objects\
                .filter(medicines__code='r', \
                        encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

    def _add_number_zinc(self, name='', line=''):
        """ Number of Zinc """

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            month = name\
                .objects\
                .filter(medicines__code='r', \
                        encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

    def _add_underfive_muac(self, name='', line=''):
        """ Number of Under Five screened for MUAC """

        list_ = []
        list_.append(line)

        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_five(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u, \
                       encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)


    def _add_underfive_muac_maln(self, name='', line=''):
        '''Number of those U5 screened who have reading of 120 and + mm '''

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_five(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u,\
                    encounter__encounter_date__gte=sp.start,\
                    encounter__encounter_date__lte=sp.end,\
                    muac__gte=120)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)


    def _add_underfive_muac_mid(self, name='', line=''):
        '''
        Number of those U5 screened who have reading of 
        less than 120 but more than 115mm
        '''

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_five(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u, \
                        encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end, \
                       muac__gt=115, muac__lt=120)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

        
    def _add_underfive_muac_small(self, name='', line=''):
        '''Number of those U5 screened who have reading of less than 115mm '''

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_five(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u, \
                        encounter__encounter_date__gte=sp.start,\
                        encounter__encounter_date__lte=sp.end, \
                        muac__lt=115)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

    def _add_underone_muac(self, name='', line=''):
        '''
        Number of Under-1 children screened with MUACs
        '''

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            month = name\
                .objects\
                .filter(encounter__encounter_date__gte=sp.start,\
                       encounter__encounter_date__lte=sp.end)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)
        
    def _add_underone_muac_maln(self, name='', line=''):
        '''
        Number of those U1 screened who have reading of 120 and + mm
        ''' 

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_one(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u,\
                    encounter__encounter_date__gte=sp.start,\
                    encounter__encounter_date__lte=sp.end,\
                    muac__gte=120)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)
       
    def _add_underone_muac_mid(self, name='', line=''):
        '''
        Number of those U1 screened who have reading 
        of less than 120 but more than 115mm 
        '''

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_one(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u,\
                    encounter__encounter_date__gte=sp.start,\
                    encounter__encounter_date__lte=sp.end,\
                    muac__gt=115,muac__lt=120)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

    def _add_underone_muac_small(self, name='', line=''):
        '''
        Number of those U1 screened who have reading of less than 115mmrow)
        '''

        list_ = []
        list_.append(line)
        
        list_month = []
        for sp in self.period.sub_periods():
            u = date_under_one(sp.end)
            month = name\
                .objects\
                .filter(encounter__patient__dob__gt=u,\
                    encounter__encounter_date__gte=sp.start,\
                    encounter__encounter_date__lte=sp.end,\
                    muac__lt=115)
            list_month.append(month.count())

        list_ += list_month
        list_text = textify_list(list_)
        self.table.add_row(list_text)

