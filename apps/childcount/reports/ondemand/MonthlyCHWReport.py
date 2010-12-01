#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.models import CHW
from childcount.models.reports import HouseholdVisitReport
from childcount.models.reports import FamilyPlanningReport
from childcount.models.ccreports import MonthlyCHWReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.utils import reporting_week_monday
from childcount.reports.utils import reporting_week_sunday
from childcount.reports.indicator import Indicator
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"Monthly CHW Report")
    filename = 'monthly_chw_report'
    formats = ['pdf','xls','html']

    def _reporting_week_date_str(self, week_num):
        return 'Wk of '+reporting_week_monday(week_num)\
            .strftime('%e %b')

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)

        for chw in MonthlyCHWReport.objects.filter(is_active=True, pk=74):
            doc.add_element(Section(chw.full_name())) 
            doc.add_element(Paragraph("For days %(start)s - %(end)s" %\
                {'start': reporting_week_monday(0).strftime('%e %B %Y'),\
                'end': reporting_week_sunday(3).strftime('%e %B %Y')}))

            table = Table(6)
            table.add_header_row([
                Text(u'Indicator'),
                Text(self._reporting_week_date_str(0)),
                Text(self._reporting_week_date_str(1)),
                Text(self._reporting_week_date_str(2)),
                Text(self._reporting_week_date_str(3)),
                Text(u'Tot/Avg'),
            ])

            for row in chw.report_rows():
                ind = Indicator(*row)
                table.add_row(map(Text,[ind.title, ind.for_week(0), ind.for_week(1),
                    ind.for_week(2), ind.for_week(3), ind.for_month()]))

            doc.add_element(table)

            table2 = Table(4, \
                Text(u"Children 1-2 years old needing immunizations"))
            table2.add_header_row([
                Text(u"Loc Code"),
                Text(u"Health ID"),
                Text(u"Name / Age"),
                Text(u"Household Head"),
            ])
            for kid in chw.needing_immunizations():
                table2.add_row([
                    Text(kid.location.code),
                    Text(kid.health_id.upper()),
                    Text(kid.full_name() + u" / " + kid.humanised_age()),
                    Text(kid.household.full_name())])
                    
            doc.add_element(table2)

            table3 = Table(5, \
                Text(_(u"Women in 2nd and 3rd Trimester who haven't had ANC in 5 Weeks")))
            table3.add_header_row([
                Text(u"Loc Code"),
                Text(u"Health ID"),
                Text(u"Name / Age"),
                Text(u"Approx Due Date"),
                Text(u"Household Head"),
            ])
            for pair in chw.pregnant_needing_anc():
                (woman, due_date) = pair
                table3.add_row([
                    Text(woman.location.code),
                    Text(woman.health_id.upper()),
                    Text(woman.full_name() + ' / ' + kid.humanised_age()),
                    Text(due_date.strftime('%Y-%B-%d')),
                    Text(woman.household.full_name())])
                    
            doc.add_element(table3)
        return render_doc_to_file(filepath, rformat, doc)


