#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: alou

import calendar

from datetime import datetime, date

import numpy

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Paragraph, Text, Section

from logger_ng.models import LoggedMessage

from reportgen.utils import render_doc_to_file

from childcount.models import Patient, DeadPerson, Encounter
from childcount.models.reports import (BirthReport, FollowUpReport,
                                   HouseholdVisitReport, DeathReport,
                                   MedicineGivenReport, PregnancyReport,
                                   HIVTestReport, AntenatalVisitReport,
                                   NutritionReport, NeonatalReport,
                                   PregnancyRegistrationReport,
                                   ReferralReport, UnderOneReport,
                                   SickMembersReport, DBSResultReport,
                                   BCPillReport, FamilyPlanningReport,
                                   DangerSignsReport, FeverReport,
                                   AppointmentReport, CD4ResultReport,
                                   StillbirthMiscarriageReport)
from reportgen.PrintedReport import PrintedReport


def agg_lst(agg_fun, lst, exclude_zeros=False):
    lst = map(lambda x: x if (type(x) in [int, float]) else 0, lst)
    if len(lst) == 0: return '-'
    return int(agg_fun(lst))


def list_average(lst, exclude_zeros=False):
    return agg_lst(numpy.average, lst, exclude_zeros)


def list_median(lst, exclude_zeros=False):
    return agg_lst(numpy.median, lst, exclude_zeros)


def date_under_five():
    """ Returns the date reduced by five years """
    today = date.today()
    date_under_five = date(today.year - 5, today.month, today.day)
    return date_under_five


def clean_list(values):
    """ Cleans a list """
    if '-' in values:
        values = [0 if v == '-' else v for v in values]
    return values


def convert_string(va1, va2):
    if va1 == 0 and va2 == 0:
        r = 0
    else:
        r = '%s/%s' % (va1, va2)
    return r


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


class ReportDefinition(PrintedReport):
    title = 'Utilization Report'
    filename = 'utilization_report'
    formats = ['html', 'pdf', 'xls']
    #variants = [('First','_first', {}),
    #    ('Second', '_second', {})]
    variants = []

    def generate(self, time_period, rformat, title, filepath, data):
        """ Display a statistic per month about:

            * sms number
            * Days since last SMS
            * NUMBER of Patient registered
            * Adult Women registered
            * Adult Men registered
            * Under Five registered
            * Number of sms error
            * +NEW, BIR, DDA, DDB, SBM, V, E, L, K, U, S, P, N, T, M, F,
            G, R, PD, PF, HT, AP, CD, DB """

        self.set_progress(0)
        doc = Document(title,
            subtitle=time_period.title, \
            landscape=True)
        self.period = time_period
        print self.period.title
        print self.period.sub_periods()

        header_row = [Text(_(u'Indicator:'))]

        for sub_period in time_period.sub_periods():
            header_row.append(Text(sub_period.title))

        header_row += [
            Text(_(u'Total')),
            Text(_(u'Average')),
            Text(_(u'Median'))]

        self.table = Table(header_row.__len__())
        self.table.add_header_row(header_row)

        self.set_progress(10)

        # first column is left aligned
        self.table.set_alignment(Table.ALIGN_LEFT, column=0)
        # first column has width of 20%
        self.table.set_column_width(13, column=0)

        # Date at which people are more than 5 years old
        self.date_five = date_under_five()

        # SMS number per month
        self._add_sms_number_per_month_row()

        self.set_progress(20)

        # NUMBER of Patient registered PER MONTH
        self._add_number_patient_reg_month_row(Patient, \
                                                      _(u"Total Clients Reg."))

        # Days since last SMS
        self._add_days_since_last_sms_month_row()

        # % of days with SMS / month
        self._of_days_with_SMS_month_row()

        self.set_progress(30)

        # Adult Women registered
        self._add_adult_registered_row('F')

        # Adult Men registered
        self._add_adult_registered_row('M')

        # Under Five registered
        self._add_under_five_registered_row()

        # Number of sms error per month
        self._add_sms_error_per_month_row()

        self.set_progress(40)
        # +NEW
        self._add_number_patient_reg_month_row(Patient, _(u"+NEW (Patient)"))

        # +BIR
        self._add_reg_report_row(BirthReport, _(u"+BIR (Birth)"))

        # +DDA
        self._add_reg_report_row(DeathReport, _(u"+DDA (Death)"))

        # +DDB
        self._add_number_patient_reg_month_row(DeadPerson, _(u"+DDB (Dead Person)"))

        # +SBM
        self._add_reg_report_row(StillbirthMiscarriageReport, _(u"+SBM (Still Birth misc)"))

        # +V
        self._add_reg_report_row(HouseholdVisitReport, _(u"+V (Household Visit)"))

        # +E
        self._add_reg_report_row(SickMembersReport, _(u"+E (Sick Members)"))

        self.set_progress(50)
        # +L
        self._add_reg_report_row(BCPillReport, _(u"+L (BC Pill)"))

        # +K
        self._add_reg_report_row(FamilyPlanningReport, _(u"+K (Family Planning)"))

        # +U
        self._add_reg_report_row(FollowUpReport, _(u"+U (Follow Up)"))

        # +S
        self._add_reg_report_row(DangerSignsReport, _(u"+S (Danger Signs)"))

        # +P
        self._add_reg_report_row(PregnancyReport, _(u"+P (Pregnancy)"))

        # +N
        self._add_reg_report_row(NeonatalReport, _(u"+N (Neonatal)"))

        # +T
        self._add_reg_report_row(UnderOneReport, _(u"+T (Under One)"))

        self.set_progress(60)
        # +MFeverReport
        self._add_reg_report_row(NutritionReport, _(u"+M (Nutrition)"))

        # +F
        self._add_reg_report_row(FeverReport, _(u"+F (Fever)"))

        # +G
        self._add_reg_report_row(MedicineGivenReport, _(u"+G (Medicine Given)"))

        # +R
        self._add_reg_report_row(ReferralReport, _(u"+R (Referral)"))

        # +PD
        self._add_reg_report_row(PregnancyRegistrationReport, _(u"+PD (Pregnancy Reg)"))

        # +PF
        self._add_reg_report_row(AntenatalVisitReport, _(u"+PF (Antenatal Visit)"))

        # +Ht
        self._add_reg_report_row(HIVTestReport, _(u"+HT (HIV Test)"))

        self.set_progress(70)
        # +AP
        self._add_reg_report_row(AppointmentReport, _(u"+AP (Appointment)"))

        # +CD
        self._add_reg_report_row(CD4ResultReport, _(u"+CD (CD4 Result)"))

        # +DB
        self._add_reg_report_row(DBSResultReport, _(u"+DB (DBS Result)"))

        doc.add_element(self.table)

        self.set_progress(80)
        return render_doc_to_file(filepath, rformat, doc)

    def _add_sms_number_per_month_row(self):
        """ SMS number per month """

        list_sms = []
        list_sms_month = []
        list_sms_debackend_month = []
        list_sms_pygsm_month = []

        list_sms.append("SMS sent(SMS/Dataentry).")

        for sp in self.period.sub_periods():
            sms_month_pygsm = LoggedMessage.incoming.\
                        filter(backend='pygsm', date__gte=sp.start, date__lte=sp.end)
            sms_month_debackend = LoggedMessage.incoming.\
                        filter(backend='debackend', date__gte=sp.start, date__lte=sp.end)

            list_sms_month.append(convert_string(sms_month_pygsm.count(),
                                       sms_month_debackend.count()))

            list_sms_pygsm_month.append(sms_month_pygsm.count())
            list_sms_debackend_month.append(sms_month_debackend.count())

        list_sms += list_sms_month

        total_pygsm = LoggedMessage.incoming.filter(backend='pygsm').count()
        total_debackend = LoggedMessage.incoming.filter(backend='debackend').count()

        list_sms.append(convert_string(total_pygsm, total_debackend))

        average_pygsm = list_average(list_sms_pygsm_month, True)
        average_debackend = list_average(list_sms_debackend_month, True)

        list_sms.append(convert_string(average_pygsm, average_debackend))

        median_pygsm = list_median(list_sms_pygsm_month, True)
        median_debackend = list_median(list_sms_debackend_month, True)

        list_sms.append(convert_string(median_pygsm, median_debackend))

        list_sms_text = textify_list(list_sms)
        self.table.add_row(list_sms_text)

    def _add_number_patient_reg_month_row(self, name, line=''):
        """ Patient, Dead Patient registered per month

            Params:
                * report name
                * indicator """

        list_patient = []
        list_patient.append(line)

        list_patient_month = []
        for sp in self.period.sub_periods():
            patient_month = name.objects.\
                filter(created_on__gte=sp.start, created_on__lte=sp.end)
            list_patient_month.append(patient_month.count())

        list_patient += list_patient_month

        total = name.objects.all().count()
        list_patient.append(total)

        average = list_average(list_patient_month, True)
        list_patient.append(average)

        median = list_median(list_patient_month, True)
        list_patient.append(median)

        list_patient_text = textify_list(list_patient)
        self.table.add_row(list_patient_text)

    def _add_reg_report_row(self, name='', line=''):
        """ Registered reports per month

            Params:
            * report name
            * indicator """

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

        total = name.objects.all().count()
        list_.append(total)

        average = list_average(list_month, True)
        list_.append(average)

        median = list_median(list_month, True)
        list_.append(median)

        list_text = textify_list(list_)
        self.table.add_row(list_text)

    def _add_days_since_last_sms_month_row(self):
        """ Days since last SMS """

        list_date = []
        list_sms = []
        total_date = 0
        list_sms.append("Days since last SMS.")
        date_ = datetime.today()

        for sp in self.period.sub_periods():
            sms_per_month = \
                    LoggedMessage.incoming.filter(date__gte=sp.start,\
                                                        date__lte=sp.end)

            try:
                lastsms = sms_per_month.order_by("-date")[0]
                ldate = (date_ - lastsms.date).days
                total_date += int(ldate)
            except:
                ldate = '-'
            list_date.append(ldate)

        list_sms += list_date
        list_sms.append(total_date)

        average_date = list_average(list_date, True)
        list_sms.append(average_date)

        median_date = list_median(list_date, True)
        list_sms.append(median_date)

        list_sms_ = textify_list(list_sms)
        self.table.add_row(list_sms_)

    def _add_adult_registered_row(self, gender):
        """ Adult registered

            Params:
                * gender """

        list_adult = []
        list_adult_month = []

        if gender == 'M':
            list_adult.append(_(u"Adult Men Reg."))
        elif gender == 'F':
            list_adult.append(_(u"Adult Women Reg."))
        else:
            return

        for sp in self.period.sub_periods():
            adult_month = Patient.objects.filter(gender=gender,
                                        created_on__gte=sp.start,\
                                        created_on__lte=sp.end,
                                        dob__lt=self.date_five)
            list_adult_month.append(adult_month.count())

        list_adult += list_adult_month

        total = Patient.objects.filter(dob__lt=self.date_five,
                                       gender=gender).count()
        list_adult.append(total)

        average = list_average(list_adult_month, True)
        list_adult.append(average)

        median = list_median(list_adult_month, True)
        list_adult.append(median)

        list_adult_text = textify_list(list_adult)
        self.table.add_row(list_adult_text)

    def _add_under_five_registered_row(self):
        """ Under five registered per month """

        under_five_list = []
        under_five_list.append(_(u"Under 5 Registered."))
        u = date_under_five()
        list_of_under_five_per_month = []
        for sp in self.period.sub_periods():
            under_five = Patient.objects.filter(dob__gt=u,
                                        created_on__gte=sp.start,\
                                        created_on__lte=sp.end)

            list_of_under_five_per_month.append(under_five.count())

        under_five_list += list_of_under_five_per_month

        total = Patient.objects.filter(dob__gt=u).count()
        under_five_list.append(total)

        average = list_average(list_of_under_five_per_month, True)
        under_five_list.append(average)

        median = list_median(list_of_under_five_per_month, True)
        under_five_list.append(median)

        list_under_five_text = textify_list(under_five_list)
        self.table.add_row(list_under_five_text)

    def _add_sms_error_per_month_row(self):
        """ SMS error per month """

        list_error = []
        list_sms_error_rate_month = []

        list_error.append(_(u"SMS error rate."))

        for sp in self.period.sub_periods():

            error_month = LoggedMessage.outgoing.\
                        filter(date__gte=sp.start, date__lte=sp.end,\
                        status="error")
            total_sms_month = LoggedMessage.incoming.\
                              filter(date__gte=sp.start, date__lte=sp.end).count()
            try:
                list_sms_error_rate_month.append((error_month.count()\
                                            * 100) / total_sms_month)
            except ZeroDivisionError:
                list_sms_error_rate_month.append(0)

        list_error += list_sms_error_rate_month

        total_error = LoggedMessage.outgoing.filter(status="error").count()
        total_sms = LoggedMessage.incoming.all().count()
        sms_error_rate = (total_error * 100) / total_sms
        list_error.append(sms_error_rate)

        average = list_average(list_sms_error_rate_month, True)
        list_error.append(average)

        median = list_median(list_sms_error_rate_month, True)
        list_error.append(median)

        list_error_text = textify_list(list_error)
        self.table.add_row(list_error_text)

    def _of_days_with_SMS_month_row(self):
        """ % of days with SMS / month """

        list_sms = []
        liste_day_rate = []
        total_day = 0
        list_sms.append(_(u"% of days with SMS / month."))

        for sp in self.period.sub_periods():
            liste_day_month = []
            sms_per_month =\
                    LoggedMessage.incoming.filter(date__gte=sp.start,\
                                                        date__lte=sp.end)
            for sms in sms_per_month:
                liste_day_month.append(sms.date.day)

            list_nb_day_month = dict().fromkeys(liste_day_month).keys()
            nb_day_per_month = len(list_nb_day_month)
            try:
                rate_day = (nb_day_per_month * 100) / (sp.end - sp.start).days
            except ZeroDivisionError:
                rate_day = (nb_day_per_month * 100) / 1

            total_day += nb_day_per_month
            print total_day
            liste_day_rate.append(rate_day)

        sms_per_year = LoggedMessage.incoming.filter(date__gte=self.period.start,\
                            date__lte=self.period.end)

        list_sms += liste_day_rate
        total_rate = (total_day * 100) / (self.period.end - self.period.start).days
        list_sms.append(total_rate)

        average_date = list_average(liste_day_rate, True)
        list_sms.append(average_date)

        median_date = list_median(liste_day_rate)
        list_sms.append(median_date)

        list_rate = textify_list(list_sms)
        self.table.add_row(list_rate)
