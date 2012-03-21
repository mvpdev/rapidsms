#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from datetime import datetime, timedelta

from django.db.models import F
from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Paragraph,\
    Text, Section, PageBreak

from childcount.models import CHW, Clinic
from childcount.indicators import household
from childcount.indicators import registration
from childcount.indicators import pregnancy

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport


class ReportDefinition(PrintedReport):
    title = u"CHW Household Visits Coverage Report"
    filename = 'chw_hh_visits_coverage_'
    formats = ['xls', 'pdf', 'html']
    variants = [(c.name, c.code, {'clinic_pk': c.pk})\
    for c in Clinic.objects.all()]

    def generate(self, period, rformat, title, filepath, data):
        # Make sure that user passed in a clinic
        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')
        clinic_pk = data['clinic_pk']

        self._period = period
        self._sub_periods = period.sub_periods()
        self._ncols = len(self._sub_periods) + 3

        doc = Document(title, period.title)
        doc.add_element(PageBreak())

        chws = CHW\
        .objects\
        .filter(clinic__pk=clinic_pk, is_active=True)

        total = chws.count()
        for i,chw in enumerate(chws):
            self.set_progress(100.0*i/total)

            doc.add_element(Section(chw.full_name()))

            # Time period string
            doc.add_element(Paragraph(_(u"For: %s") % period.title))

            doc.add_element(self._household_visits_coverage(chw))

            doc.add_element(PageBreak())

        return render_doc_to_file(filepath, rformat, doc)

    def _household_visits_coverage(self, chw):
        households = chw.patient_set.filter(pk=F('household__pk'))
        patients = chw.patient_set.all()
        num_u5 = registration.UnderFive(self._period, patients)
        num_pregnant = pregnancy.Total(self._period, patients)
        title = _(u"Total number of HH assigned: %(num)s \t" % \
                  {'num': households.count()})
        title += _(u"Total Number of Under-5s: %(num)s \t" % {'num': num_u5})
        title += _(u"Total Number of Pregnant Women: %(num)s" % \
                   {'num': num_pregnant})
        table = Table(self._ncols, title=Text(title))

        headers = [_(u"HH ID"), _(u"NAME OF HOUSEHOLD HEAD"), _("LOCATION")]
        headers += [sp.title for sp in self._period.sub_periods()]

        table.add_header_row(map(Text, headers))

        for i in xrange(0, len(self._sub_periods)):
            table.set_column_width(12, i+1)
        table.set_column_width(18, self._ncols-1)

        table.add_row([Text(" ")] * self._ncols)
        # For each household ...
        for hh in households:
            data_row = [Text(hh.health_id)]
            data_row += [Text(hh.full_name())]
            data_row += [Text(hh.location)]
            data_row += [Text(household.Total(sp, \
                        chw.patient_set.filter(pk=hh.pk)))\
                        for sp in self._sub_periods]
            table.add_row(data_row)
        return table