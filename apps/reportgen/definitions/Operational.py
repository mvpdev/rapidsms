#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import copy
from datetime import datetime

from django.utils.translation import ugettext as _

try:
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
from childcount.models import Patient
from childcount.models import CHW
from childcount.helpers.chw import report_indicators as chw_report_indicators

from childcount.utils import RotatedParagraph

from libreport.pdfreport import p

import bonjour.dates

from ccdoc.utils import register_fonts
from reportgen.PrintedReport import PrintedReport
from reportgen.utils import render_doc_to_file

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleH3 = styles['Heading3']
styleH3.fontName = 'FreeSerif'

class ReportDefinition(PrintedReport):
    title = 'Operational Report'
    filename = 'operational_report'
    formats = ('pdf',)

    variants = [(c.name, c.code, {'clinic_pk': c.pk}) \
                                    for c in Clinic.objects.all()]

    def generate(self, period, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for operational report')

        self.set_progress(0.0)

        self._indicators = chw_report_indicators()

        story = []

        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')

        clinic_pk = data['clinic_pk']
        location = Clinic\
            .objects\
            .get(pk=clinic_pk)

        chws = CHW\
                    .objects\
                    .filter(is_active=True)\
                    .filter(clinic=location)

        tb = self._operationalreportable(period, location, chws)

        story.append(tb)
        story.append(PageBreak())

        register_fonts()
        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)
        f.close()

    def _operationalreportable(self, period, title, chws):
        tStyle = [('INNERGRID', (0, 0), (-1, -1), 0.1, colors.lightgrey),\
                ('BOX', (0, 0), (-1, -1), 0.1, colors.lightgrey)]
        rowHeights = []
        styleH3.fontName = 'FreeSerif'
        styleH3.alignment = TA_CENTER
        styleH3.fontSize = 10

        ''' Header data '''
        now = datetime.now()
        hdata = [Paragraph(_(u'<b>%(name)s - %(title)s '\
                                '(Generated on '\
                                '%(gen_datetime)s)</b>')% \
                                {'name': title,\
                                'title': period.title,\
                                'gen_datetime': bonjour.dates.format_datetime(format='medium')},
                styleH3)]
        tStyle.append(('SPAN', (0, 0), (-1, 0)))

        ncols = sum([len(c['columns']) for c in self._indicators])
        hdata.extend((ncols - 1) * [''])
        rowHeights.append(None)
        data = [hdata]

        group_row = ['']
        thirdrow = [Paragraph(_('<b>CHW Name</b>'), styleH3)]

        # Row index
        index = 1

        # Col index
        i = 0

        colWidths = [1.4 * inch]
        for g in self._indicators:
            group_len = len(g['columns'])
            
            # Title string
            group_row.append(Paragraph(u'<b>'+g['title']+u'</b>', styleH3))
            group_row.extend([''] * (group_len - 1))

            # Add a box around odd-indexed column groups
            if i % 2 == 1:
                tStyle.append(('BOX', (index, 1), (index + group_len - 1, -1), \
                                        2, colors.lightgrey))
            tStyle.append(('SPAN', (index, 1), (index + group_len - 1, 1)))
            index += group_len
            i += 1

            # Column headers
            for col in g['columns']:
                p = RotatedParagraph(Paragraph((col['name']), styleN), \
                    2.3*inch, 0.25*inch)
                thirdrow.append(p)

                # Give percentages wide columns
                colWidths.append((0.4 * inch))

        data.append(group_row)
        rowHeights.append(None)

        data.append(thirdrow)
        rowHeights.append(2.3*inch)
    
        def format_val(ind, val):
            if ind.output_is_percentage():
                return val.short_str()
            else:
                return unicode(val)

        count_chws = chws.count()
        count_inds = len(self._indicators)
        total = (count_chws+1) * count_inds
        current = 0.0

        if count_chws > 0:
            self.set_progress((100.0*current)/total)
            rows = []

            for chw in chws:
                row = [Paragraph(chw.full_name(), styleN)]

                for group in self._indicators:
                    current += 1.0

                    for pair in group['columns']:
                        print pair['name']
                        value = pair['ind'](period, chw.patient_set.all())
                        row.append(Paragraph(format_val(pair['ind'], value), styleN))
                    self.set_progress((100.0*current)/total)

                rows.append(row)
         
            # Get totals for the clinic
            patients = Patient.objects.filter(chw__clinic__pk=chws[0].clinic.pk)
            row = [Paragraph(u"<b>" + chw.clinic.name + u"</b>", styleN)]
            for group in self._indicators:
                self.set_progress((100.0*current)/total)
                current += 1
                for pair in group['columns']:
                    print pair['name']
                    value = pair['ind'](period, patients)
                    row.append(Paragraph(format_val(pair['ind'], value), styleN))
            rows.append(row)

            rowHeights.extend(len(rows) * [0.25 * inch])

            # Add data to table
            data.extend(rows)
            tStyle.append(('LINEABOVE', (0, 3), (-1, 3), 0.5, colors.black))
            tStyle.append(('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black))

        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tb.setStyle(TableStyle(tStyle)) 
        
        return tb
