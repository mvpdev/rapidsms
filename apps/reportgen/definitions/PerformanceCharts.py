#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from fractions import Fraction

from django.utils.translation import ugettext as _

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch

from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus import Table

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.legends import Legend

from childcount.indicators import nutrition
from childcount.indicators import under_one
from childcount.indicators import pregnancy
from childcount.indicators import follow_up

from childcount.models import Clinic
from childcount.models import Patient

from childcount.helpers import site

from ccdoc.utils import register_fonts

import bonjour.dates

from reportgen.PrintedReport import PrintedReport

register_fonts()

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleH = styles['Heading1']
styleN.fontName = 'FreeSerif'
styleH3 = styles['Heading2']
styleN.fontName = 'FreeSerif'
styleH3.alignment = 1

class ReportDefinition(PrintedReport):
    title = _(u'Performance Charts')
    filename = 'performance_charts'
    formats = ('pdf',)

    _indicators = site.key_indicators()

    def generate(self, period, rformat, title, filepath, data):
        if rformat != 'pdf':
            raise NotImplementedError(\
                _(u'Can only generate PDF for performance charts'))

        story = [Paragraph(unicode(title), styleH),\
            Paragraph(_("Generated on: ") + 
                bonjour.dates.format_datetime(format='full'), styleN),\
            Paragraph(_("For period %s.") % period.title, styleN)]

        clinics = Clinic\
            .objects\
            .order_by('name')\
            .exclude(code='ZZZZ')

        self._sub_periods = period.sub_periods()
        self._sub_periods.reverse()

        table_data = [[]]

        # data[t][c] should be the value at time period t of
        # an indicator at clinic c
        self.set_progress(0.0)
        total = len(self._indicators) * len(self._sub_periods) * clinics.count()
        i=0
        for i,ind in enumerate(self._indicators):
            title = ind.long_name

            # Initialize data structure
            data = []
            for t,sp in enumerate(self._sub_periods):
                data.append([])

            for t_index, sub_period in enumerate(self._sub_periods):
                for c_index, c in enumerate(clinics):
                    val = ind(sub_period, Patient.objects.filter(chw__clinic=c))

                    data[t_index].append(val)

                    i+=1
                    self.set_progress((100.0*i)/total)
          
            graph = self._graph(data, [c.name for c in clinics], period)
            flowable = [Paragraph(title, styleH3), graph]

            last_row = table_data[len(table_data)-1]
            if len(last_row) < 2:
                last_row.append(flowable)
            else:
                table_data.append([flowable])

        story.append(Table(table_data, \
            style = [\
                ('ALIGN', (0,0), (-1, -1), 'CENTER'),\
                ('VALIGN', (0,0), (-1, -1), 'CENTER'),\
                ('LEFTPADDING', (0,0), (-1, -1), 15),\
                ('RIGHTPADDING', (0,0), (-1, -1), 15),\
                ('TOPPADDING', (0,0), (-1, -1), 15),\
                ('BOTTOMPADDING', (0,0), (-1, -1), 15),\
            ]))

        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0.1 * inch), \
                                bottomMargin=(0.1 * inch),\
                                leftMargin=(0.1 * inch),\
                                rightMargin=(0.1 * inch))
                                
        doc.build(story)
        f.close()

    def _graph(self, data, labels, period_set):
        dh = 2.2 * inch
        dw = 4 * inch

        drawing = Drawing(dw, dh)

        bc = HorizontalBarChart()
        bc.setProperties({
            'x': 0.5 * inch,
            'y': 0 * inch,
            'height': dh - (0 * inch),
            'width': dw - (1.4 * inch),
            'data': data,
            'strokeWidth': 0,
            'barLabelFormat': self._perc_str,
        })
        bc.valueAxis.setProperties({
            'forceZero': 1,
            'valueMin': 0,
            'valueMax': 1,
            'labelTextFormat': lambda p: "%d%%"%(100*p),
        })
        bc.categoryAxis.setProperties({
            'categoryNames': labels,
        })

        if len(data) > 0:
            bc.bars[0].fillColor = colors.Color(0.2,0.2,0.2, 1)
        if len(data) > 1:
            bc.bars[1].fillColor = colors.Color(0.7,0.7,0.7, 1)
            bc.bars[1].strokeDashArray = [2,2]

        from pprint import pprint
        pprint(bc.bars.getProperties())
        drawing.add(bc)

        legend = Legend()
        legend.x = dw
        legend.y = dh
        legend.colorNamePairs = []
        legend.boxAnchor = 'nw'
        for i in xrange(0, len(data)):
            legend.colorNamePairs.append(\
                (bc.bars[i].fillColor, self._sub_periods[i].title))
        pprint(legend.getProperties())

        # For some reason these get drawn in the opposite
        # order as the bars by default
        legend.colorNamePairs.reverse()
        drawing.add(legend)

        return drawing
    
    def _perc_str(self, perc):
        s = unicode(perc)
        l = (len(s)*2) + 3

        return (u" " * l) + s
