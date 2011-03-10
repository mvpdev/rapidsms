#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy
import numpy

from django.utils.translation import gettext as _
from django.template import Template, Context
from locations.models import Location

try:
    import reportlab
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
    from reportlab.platypus import Table, TableStyle, NextPageTemplate
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

from childcount.models import Clinic
from childcount.models import CHW
from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import OperationalReport
from childcount.utils import RotatedParagraph
from childcount.reports.utils import render_doc_to_file

from libreport.pdfreport import p

from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']


def message_text(text):
    return Paragraph(text, styleN)

_variants = map(lambda c: \
        (unicode(c), '_' + c.code + '_clinic', {'clinic_pk': c.pk, \
                                          'type_str': 'clinic', \
                                          'type_obj': Clinic}),
        Clinic.objects.all())

_variants += map(lambda c: \
        (unicode(c), '_' + c.code + '_location', {'clinic_pk': c.pk, \
                                          'type_str': 'clinic', \
                                          'type_obj': Location}),
        Location.objects\
            .filter(pk__in=CHW.objects\
                                .values('location').distinct('location')))


class Report(PrintedReport):
    title = _(u"CHW Management Report")
    filename = 'operational_report'
    formats = ('pdf',)
    '''
    variants = [ \
        (_(u" (By Clinic)"), '_clinic', \
            {'type_str': 'clinic', 'type_obj': Clinic}), \
        (_(" (By Location)"), '_location', 
            {'type_str': 'location', 'type_obj': Location}), \
    ]'''
    variants = _variants

    def generate(self, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for operational report')
        print "in here", data
        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')
        clinic_pk = data['clinic_pk']
        f = open(filepath, 'w')

        type_str = data['type_str']
        type_obj = data['type_obj']

        story = []
        locations = type_obj.objects.filter(pk=clinic_pk)

        for location in locations:
            filter_on = {type_str: location}
            if not TheCHWReport\
                    .objects\
                    .filter(is_active=True)\
                    .filter(**filter_on).count():
                continue
            tb = self._operationalreportable(location, \
                                   TheCHWReport.objects.filter(is_active=True)\
                                                       .filter(**filter_on))
            story.append(tb)
            story.append(PageBreak())

        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))

        # add blank page if no data
        # so that pdf is valid
        if story.__len__() == 0: story.append(message_text(\
                                 _(u"There is no data mathcing this report.")))

        try:
            doc.build(story)
        except Exception as e:
            doc.build([message_text(_(u"There has been an error generating " \
                                   u"this report: %s") % e)])
            raise

        f.close()

    def _operationalreportable(self,title, indata=None):
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleH3.fontSize = 10
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        opr = OperationalReport()
        cols = opr.get_columns()

        ''' Header data '''
        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        data = [hdata, ['', Paragraph(_(u"Household"), styleH3), '', '', \
                Paragraph(_(u"Newborn"), styleH3), '', '', \
                Paragraph(_(u"Under-5's"), styleH3), '', \
                '', '', '', '', Paragraph(_(u"Pregnant"), styleH3), '', '', \
                Paragraph(_(u"Appointment"), styleH3), '', \
                Paragraph(_(u"Follow-up"), styleH3), '', \
                Paragraph(_(u"SMS"), styleH3), '', \
                Paragraph('',
                            styleH3)], \
                ['', Paragraph(_(u"A1"), styleH3), Paragraph(_(u"A2"), styleH3), \
                Paragraph(_(u"A3"), styleH3), Paragraph(_(u"B1"), styleH3), \
                Paragraph(_(u"B2"), styleH3), Paragraph(_(u"B3"), styleH3), \
                Paragraph(_(u"C1"), styleH3), Paragraph(_(u"C2"), styleH3), \
                Paragraph(_(u"C3"), styleH3), Paragraph(_(u"C4"), styleH3), \
                Paragraph(_(u"C5"), styleH3), Paragraph(_(u"C6"), styleH3), \
                Paragraph(_(u"D1"), styleH3), Paragraph(_(u"D2"), styleH3), \
                Paragraph(_(u"D3"), styleH3), Paragraph(_(u"E1"), styleH3),
                Paragraph(_(u"E2"), styleH3), Paragraph(_(u"F1"), styleH3), \
                Paragraph(_(u"F2"), styleH3), Paragraph(_(u"G1"), styleH3), \
                Paragraph(_(u"G2"), styleH3), Paragraph(_(u"H1"), styleH3)]]

        thirdrow = [Paragraph(cols[0]['name'], styleH3)]
        thirdrow.extend([RotatedParagraph(Paragraph(col['name'], styleN), \
                                    2.3 * inch, 0.25 * inch) for col in cols[1:]])
        data.append(thirdrow)

        fourthrow = [Paragraph('Target:', styleH3)]
        fourthrow.extend([Paragraph(item, styleN) for item in ['-', '-', '100', \
                            '-', '100', '100', '-', '-', '-', '-', '100', '-', \
                            '-', '-', '100', '', '100', '100', '&lt;=2', '0', \
                            '-', '100']])
        data.append(fourthrow)

        fifthrow = [Paragraph(_(u"<u>List of CHWs</u>"), styleH3)]
        fifthrow.extend([Paragraph(item, styleN) for item in [''] * 19])
        data.append(fifthrow)

        rowHeights = [None, None, None, 2.3 * inch, 0.25 * inch, 0.25 * inch]
        colWidths = [1.7 * inch]
        colWidths.extend((len(cols) - 1) * [0.4 * inch])

        ''' value_data contains the strings for each cell of the table.
            We need to format these into reportlab Paragraph objects
            with bold and underlining.

            agg_data has the summary figures for the bottom of the table.

            thresholds has a tuple (low, high) for the values below/above
            which a cell should be underlined/bolded.
        '''

        (value_data, agg_data, thresholds) = self._generate_stats(cols, indata)
        if len(value_data) > 0:
            rows = []
            for values in value_data:
                row = []

                for (i,col) in enumerate(values):
                    # CHW Name
                    if i == 0:
                        row.append(Paragraph(col, styleN))
                        continue

                    tag_open = tag_close = u''
                    colv = self._strip_junk(col)
                    # If colv is None, then the value is '-' sp
                    # don't format it.  If thresholds is None
                    # then there isn't any data to format.
                    if colv is not None and \
                            thresholds[i-1] and \
                            colv < thresholds[i-1][0]:
                        tag_open = u'<u>'
                        tag_close = u'</u>'
                    elif colv is not None and \
                            thresholds[i-1] and \
                            colv > thresholds[i-1][1]:
                        tag_open = u'<b>'
                        tag_close = u'</b>'

                    row.append(Paragraph(u"%s%s%s" % \
                        (tag_open, col, tag_close), styleN)) 
                rows.append(row)

            # Add data to table
            data.extend(rows)
            data.extend(agg_data)
            rowHeights.extend(len(indata) * [0.25 * inch])
            rowHeights.extend(3 * [0.25 * inch])

        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tstyles = []
            
            
        tstyles = [('INNERGRID', (0, 0), (-1, -1), 0.1, colors.lightgrey),
                   ('BOX', (0, 0), (-1, -1), 0.1, colors.lightgrey),
                   ('BOX', (1, 1), (3, -1), 2, colors.lightgrey),
                   ('BOX', (7, 1), (12, -1), 2, colors.lightgrey),
                   ('BOX', (16, 1), (17, -1), 2, colors.lightgrey),
                   ('BOX', (20, 1), (21, -1), 2, colors.lightgrey),
                   ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),]

        if float(reportlab.Version) >= 2.4:

            tstyles.extend([
                ('SPAN', (0, 0), (22, 0)),
                ('SPAN', (1, 1), (3, 1)), 
                ('SPAN', (4, 1), (6, 1)), 
                ('SPAN', (7, 1), (12, 1)),
                ('SPAN', (13, 1), (15, 1)),
                ('SPAN', (16, 1), (17, 1)),
                ('SPAN', (18, 1), (19, 1)),
                ('SPAN', (20, 1), (21, 1))])

        tbs = TableStyle(tstyles)
        tb.setStyle(tbs)
        return tb

    def _generate_stats(self, cols, indata):
        value_data = []
        # Get data values minus first column -- since that column
        # just has the CHW name
        aggregate_data = map(lambda x: [], cols[1:])

        if not indata:
            return ([], [], [])

        for chw in indata:
            ctx = Context({"object": chw, "zero": u'0'})

            # Render column values into strings
            row_values = map(lambda col: Template(col['bit']).render(ctx), cols)
            value_data.append(row_values)

            # Convert data to float for aggregation
            for (i,val) in enumerate(row_values[1:]):
                val = self._strip_junk(val)
                if val is not None:
                    aggregate_data[i].append(val)


        thresholds = []
        aggregates = [[_(u"Average")], [_(u"Standard Deviation")], [_(u"Median")]]
        for points in aggregate_data:
            if points:
                avg = numpy.average(points)
                std = numpy.std(points)
                med = numpy.median(points)
       

                aggregates[0].append(Paragraph(u"%0.1f" % avg, styleN))
                aggregates[1].append(Paragraph(u"%0.1f" % std, styleN))
                aggregates[2].append(Paragraph(u"%0.1f" % med, styleN))

                thresholds.append((avg - (2*std), avg + (2*std)))
            else:
                for i in xrange(0,3):
                    aggregates[i].append(u'-') 
                thresholds.append(None)

        return (value_data, aggregates, thresholds)


    def _strip_junk(self, v):
        v = v.replace('%', '').replace('-', '').replace(' ', '')
        if v == '':
            return None
        return float(v)
