#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Text, Section

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

from childcount.indicators import birth
from childcount.indicators import death

from childcount.models import Patient

class ReportDefinition(PrintedReport):
    title = _(u"Vital Events Report ")
    filename = 'Vital_events_report_'
    formats = ['pdf','html', 'xls']

    _indicators = (
            birth.Total,
            death.Neonatal,
            death.UnderOne,
            death.UnderFive,
            death.PregnancyRelated,
            death.OverFiveNotPregnancyRelated)


    def generate(self, time_period, rformat, title, filepath, data):
        
        doc = Document(title, landscape=True)

        self.set_progress(0)
 
        # Category, Descrip, Sub_Periods
        sub_periods = time_period.sub_periods()

        table = Table(1+len(sub_periods), \
            Text(_("VITAL EVENTS: %s") % time_period.title))

        table.add_header_row([Text("Indicator")] + \
            [Text(p.title) for p in time_period.sub_periods()])

        n_inds = len(self._indicators)+1
        count = 0

        patients = Patient.objects.all()

        for ind in self._indicators:
            row = []
            row.append(unicode(ind.short_name))

            for t in sub_periods:
                row.append(ind(t, patients))
          
            table.add_row([Text(c) for c in row])

            self.set_progress(100.0*count/n_inds)
            count += 1

        doc.add_element(table)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

    @classmethod
    def data_only(cls, time_period):
        sub_periods = time_period.sub_periods()
        patients = Patient.objects.all()
        data = []
        for ind in cls._indicators:
            row = []
            row.append(unicode(ind.short_name))

            for t in sub_periods:
                x = ind(t, patients)
                row.append(x)
            data.append(row)
        return data
