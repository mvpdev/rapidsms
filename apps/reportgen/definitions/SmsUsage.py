#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: alou

import calendar

from datetime import datetime, date

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Paragraph, Text, Section

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

from childcount.models import CHW
from childcount.indicators import message

from reporters.models import Reporter


class ReportDefinition(PrintedReport):
    title = 'SMS Usage'
    filename = 'sms_usage'
    formats = ['html', 'pdf', 'xls']
    variants = []

    def generate(self, time_period, rformat, title, filepath, data):
        self.set_progress(0)
        doc = Document(title,
            subtitle = time_period.title, \
            landscape=True)
        self.period = time_period
    
        header_row = [Text(_(u'CHW Name')), Text(_('Clinic'))]

        for sub_period in time_period.sub_periods():
            header_row.append(Text(sub_period.title))

        header_row += [Text(time_period.title), Text(_("% Error"))]

        self.table = Table(len(header_row))
        self.table.add_header_row(header_row)

        self.set_progress(10)

        # first column is left aligned
        self.table.set_alignment(Table.ALIGN_LEFT, column=0)
       
        # first column has width of 20%
        self.table.set_column_width(15, column=0)
        for i in xrange(0,len(time_period.sub_periods())):
            self.table.set_column_width(10, column=i+2)

        chws = CHW.objects.order_by('clinic__name','first_name')
        total = chws.count()
        for i,chw in enumerate(chws):
            row = [Text(chw.full_name()), Text(chw.clinic.code.upper() if chw.clinic else "--")]
            row += [Text("%d" % message.Sms(sp, Reporter.objects.filter(pk=chw.pk))) \
                        for sp in time_period.sub_periods()+[time_period]]
            row += [Text(message.ErrorSmsPerc(sp, Reporter.objects.filter(pk=chw.pk)).short_str())]
            self.table.add_row(row)

            self.set_progress(10+(70.0*i/total))

        total = [Text(_("All CHWs"), bold=True), Text("--", bold=True)]
        total += [Text("%d" % message.Sms(sp, Reporter.objects.all()), bold=True) \
                        for sp in time_period.sub_periods()+[time_period]]
        total += [Text(message.ErrorSmsPerc(sp, Reporter.objects.all()).short_str(), bold=True)]
        self.table.add_row(total)

        doc.add_element(self.table)

        self.set_progress(90)
        return render_doc_to_file(filepath, rformat, doc)

