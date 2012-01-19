#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _
from datetime import datetime

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

from childcount.utils import RotatedParagraph

from libreport.pdfreport import p

import bonjour.dates

from ccdoc.utils import register_fonts
from reportgen.PrintedReport import PrintedReport
from reportgen.utils import render_doc_to_file

from childcount.models import Patient, Clinic
 
from childcount.models.reports import LabReport

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleH3 = styles['Heading3']
styleH3.fontName = 'FreeSerif'


class ReportDefinition(PrintedReport):
    title = _(u"LABS IN PROGRESS ")
    filename = 'lab_report_'
    formats = ['pdf','html', 'xls']
    variants = []

    def generate(self, period, rformat, title, filepath, data):
        self.set_progress(0)
        
        story = []

        tStyle = [('INNERGRID', (0, 0), (-1, -1), 0.1, colors.lightgrey),\
                ('BOX', (0, 1), (-1, -1), 0.1, colors.lightgrey)]

        rowHeights = []
        colWidths = []
        styleH3.fontName = 'FreeSerif'
        styleH3.alignment = TA_CENTER
        styleN.alignment = TA_LEFT
        styleH3.fontSize = 10

        ''' Header data '''
        now = datetime.now()
        hdata = [Paragraph(_(u'<b>%(name)s  '\
                                '(Generated on '\
                                '%(gen_datetime)s)</b>')% \
                                {'name': title,\
                                'gen_datetime': bonjour.dates.format_datetime(format='medium')},
                styleH3)]
        tStyle.append(('SPAN', (0, 0), (-1, 0)))

        ncols = 12 #sum([len(c['columns']) for c in self._indicators])
        hdata.extend((ncols - 1) * [''])
        rowHeights.append(None)
        data = [hdata]

        
        thirdrow = [Paragraph(_('<b>Date of Req</b>'), styleH3)]
        colWidths = [1 * inch]

        thirdrow.append(Paragraph(_('<b>MVP Health ID</b>'), styleH3))
        colWidths.append((0.6 * inch))
        thirdrow.append(Paragraph(_('<b>Name</b>'), styleH3))
        colWidths.append((2.4 * inch))
        thirdrow.append(Paragraph(_('<b><b>Age</b>'), styleH3))
        colWidths.append((0.4 * inch))
        thirdrow.append(RotatedParagraph(Paragraph(_('Sex (M/F)'), \
                        styleN), 1.3*inch, 0.15*inch))
        colWidths.append((0.4 * inch))

        thirdrow.append(RotatedParagraph(Paragraph(_('<b>Requesting '\
                            'Facility</b>'), styleN), 1.4*inch, 0.15*inch))
        colWidths.append((0.4 * inch))

        thirdrow.append(RotatedParagraph(Paragraph(_('<b>Test Required </b>'), \
                        styleN),  1.4*inch, 0.15*inch))
        colWidths.append((0.4 * inch))

        thirdrow.append(Paragraph(_('<b>Sample #</b>'), styleH3))
        colWidths.append((1.4 * inch))

        thirdrow.append(RotatedParagraph(Paragraph(_('<b>Requisition ' \
                        'Progress</b>'), styleN), 1.3*inch, 0.25*inch))
        colWidths.append((0.4 * inch))

        thirdrow.append(Paragraph(_('Reg. progress Code'), styleH3))
        colWidths.append((1 * inch))

        thirdrow.append(RotatedParagraph(Paragraph(_('<b>Results</b>'), \
                        styleN), 0.4*inch, 0.25*inch))
        colWidths.append((0.4 * inch))

        thirdrow.append([Paragraph('', styleH3)])
        colWidths.append((2.4 * inch))

        
        data.append(thirdrow)
        rowHeights.append(1.7*inch)

        ''' Add elements '''
        count  = LabReport.objects.all().count()

        rows = []
        if count > 0:
            #self.set_progress((100.0*current)/total)
            http://jawbreaker88.wordpress.com/2011/12/16/chiku-weeee-never-again-try-to-bust-a-dr/
            for re in LabReport.objects.all():

                req_date = re.encounter.encounter_date.strftime("%d/%m/%y")
                row = [Paragraph(req_date, styleN)]
                #Health Id
                row.append([Paragraph(re.encounter.patient.health_id, \
                                                        styleH3)])
                #Name
                row.append([Paragraph(re.encounter.patient.full_name(), \
                                                    styleN)])
                #Humanised Age
                row.append([Paragraph(re.encounter.patient.humanised_age(), \
                                                    styleN)])
                #gender
                row.append([Paragraph(re.encounter.patient.gender, \
                                                    styleH3)])
                #Patient Clinic Tested
                row.append([Paragraph(re.encounter.chw.clinic.code, \
                                                    styleH3)])
                #Test Code
                row.append([Paragraph(re.lab_test.code, styleH3)])
                #Sample Number
                row.append([Paragraph(re.sample_no, styleH3)])

                #Progress Status
                row.append([Paragraph(_('<b>+QP</b>'), styleH3)])
                row.append([Paragraph(re.progress_status, styleH3)])

                #Results
                row.append([Paragraph(_('<b>+QR</b>'), styleH3)])
                row.append([Paragraph(re.results, styleH3)])

                rows.append(row)

       
        #Add Blank rows 
        if count%20 != 0:
            #self.set_progress((100.0*current)/total)

            for re in range(20-count%20):
                br = [Paragraph('', styleN)]
                br.append([Paragraph('', styleH3) ])
                br.append([Paragraph('', styleH3) ])
                br.append([Paragraph('', styleH3) ])
                br.append([Paragraph('', styleH3) ])
                br.append([Paragraph('', styleH3) ])
                br.append([Paragraph('', styleH3) ])
                br.append([Paragraph('', styleH3) ])
                #Progress Status
                br.append([Paragraph(_('<b>+QP</b>'), styleH3)])
                br.append([Paragraph('', styleH3) ])
                #Results
                br.append([Paragraph(_('<b>+QR</b>'), styleH3)]) 
                br.append([Paragraph('', styleH3) ])

                rows.append(br)

        rowHeights.extend(len(rows) * [0.25 * inch])

        # Add data to table
        data.extend(rows)

        tStyle.append(('BOX', (0, 1), (-1, -1), 0.5, colors.black))
        tStyle.append(('BOX', (8, 1), (8, -1), 0.5, colors.black))
        tStyle.append(('BOX', (10, 1), (10, -1), 0.5, colors.black))

        tStyle.append(('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black))
        tStyle.append(('LINEABOVE', (0, 2), (-1, 2), 0.5, colors.black))

        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tb.setStyle(TableStyle(tStyle))

        story.append(tb)
        story.append(PageBreak())

        register_fonts()
        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)
        self.set_progress(100)
        f.close()
