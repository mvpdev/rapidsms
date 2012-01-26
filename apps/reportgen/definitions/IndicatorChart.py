#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga
import copy

from django.utils.translation import ugettext as _

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch

from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus import Table

from reportlab.graphics.shapes import Drawing, String, Group
from reportlab.graphics.shapes import colors
from reportlab.graphics.charts.linecharts import HorizontalLineChart

from indicator.query_set_type import QuerySetType

from reporters.models import Reporter

import bonjour.dates

from childcount.models import Patient
from childcount.models import Clinic
from childcount.utils import get_indicators

from reportgen.PrintedReport import PrintedReport

from ccdoc.utils import register_fonts

# Load fonts compatible with Ethiopian scripts
register_fonts()

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleH = styles['Heading1']
styleH.fontName = 'FreeSerif'
styleH2 = styles['Heading2']
styleH2.alignment = 1
styleH2.fontName = 'FreeSerif'
styleH3 = styles['Heading3']
styleH3.alignment = 1
styleH3.fontName = 'FreeSerif'
styleNR = copy.copy(styles['Normal'])
styleNR.alignment = 2
styleNR.fontName = 'FreeSerif'

class ReportDefinition(PrintedReport):
    title = u'Indicator Chart'
    filename = 'indicator_chart'
    formats = ('pdf',)

    variants = sum([
                    # Make a report variant tuple for each indicator...
                    # in each indicator module
                        [(u"%s \u00BB %s" % (module['name'], ind[1].short_name), \
                            "_"+module['slug']+"_"+ind[1].slug, \
                            { 'ind_module': module['slug'], 
                                'ind_cls': ind[0]}
                        ) for ind in module['inds']]
                    for module in get_indicators()], \
                    [])

    def _data_to_ind(self, ind_module, ind_cls):
        for m in get_indicators():
            if m['slug'] == ind_module:
                for idata in m['inds']:
                    if idata[0] == ind_cls:
                        return idata[1]
        raise ValueError(_("Indicator not found!"))

    def generate(self, period, rformat, title, filepath, data):
        if rformat != 'pdf':
            raise NotImplementedError(\
                _(u'Can only generate PDF for indicator chart'))

        story = [Paragraph(u"<b>"+unicode(title)+u"</b>", styleH),\
            Paragraph(_("Generated on: ") + 
                bonjour.dates.format_datetime(format='full'), styleN),\
            Paragraph(_("For period: %s.") % period.title, styleN)]

        cat_names = []       
        graph_data = []

        ind = self._data_to_ind(data['ind_module'], data['ind_cls'])
        self._ind = ind

        things = None
        if ind.input_is_query_set:
            things = ind.type_in.mtype.objects.all()
        else:
            raise ValueError(_("Cannot produce indicator chart for "\
                            "indicators that do not accept a QuerySet "\
                            "as an argument."))

        self.set_progress(0.0)

        sub_periods = period.sub_periods()
        total = len(sub_periods)
        table_data = [[Paragraph("Time Period", styleH3),
                        Paragraph(ind.short_name, styleH3)]]
        for i,sp in enumerate(sub_periods):
            value = ind(sp, things)

            cat_names.append(sp.title)
            graph_data.append(value)

            table_data.append((Paragraph(sp.title, styleNR), 
                Paragraph(str(value), styleN)))
            self.set_progress((i*100.0)/total)

        graph = self._graph(cat_names, [graph_data], period)
        story.append(Paragraph(u"<b>" + ind.long_name + _(" over time")+u"</b>", styleH2))

        t2 = Table(table_data)
        t2.setStyle([
            ('ALIGNMENT', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ])

        t = Table([[graph, t2]])
        t.setStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP')])
        story.append(t)
        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0.1 * inch), \
                                bottomMargin=(0.1 * inch),\
                                leftMargin=(0.1 * inch),\
                                rightMargin=(0.1 * inch))
                                
        doc.build(story)
        f.close()

    def _graph(self, cat_names, data, period_set):
        dh = 4 * inch
        dw = 6 * inch

        drawing = Drawing(dw, dh)

        lp = HorizontalLineChart()
        lp.setProperties({
            'x': 0.5 * inch,
            'y': 0.5 * inch,
            'height': 3 * inch,
            'width': 5 * inch,
            'data': data,
            'strokeWidth': 0,
        })

        vAxisProperties = {
            'valueMin': 0
        }
        if self._ind.output_is_percentage():
            vAxisProperties['valueMax'] = 1.0
            vAxisProperties['labelTextFormat'] = lambda p: "%d%%"%(100*p)
                
        lp.valueAxis.setProperties(vAxisProperties)
        lp.categoryAxis.setProperties({
            'categoryNames': cat_names,
        })

        for i,v in enumerate(cat_names):
            lp.categoryAxis.labels[i].angle = 90
            lp.categoryAxis.labels[i].dy = -int(3*len(v))

        drawing.add(lp)

        return drawing
    
    def _perc_str(self, perc):
        s = unicode(perc)
        l = (len(s)*2) + 3

        return (u" " * l) + s
