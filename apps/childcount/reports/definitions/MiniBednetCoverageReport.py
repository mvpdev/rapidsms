#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy

from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.db.models import F

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter, landscape, A4
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
from childcount.models.ccreports import ThePatient
from childcount.utils import RotatedParagraph

from libreport.pdfreport import p
from libreport.pdfreport import ScaledTable

from childcount.reports.utils import report_filepath
from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()

styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = u'Bednet Survey: '
    filename = 'bn_survey'
    formats = ['pdf']
    variants = map(lambda c: \
        (unicode(c), '_'+c.code, {'clinic_pk': c.pk}),
        Clinic.objects.all())
    
    def generate(self, rformat, title, filepath, data):
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for bednet survey')

        # Make sure that user passed in a clinic 
        if 'clinic_pk' not in data:
            raise ValueError('No clinic index passed to report')

        clinic_pk = data['clinic_pk']

        # Produce the report
        f = open(filepath, 'w')
        clinic = Clinic.objects.get(pk=clinic_pk)
        self.gen_household_surveyreport(f, clinic)
        f.close()

    def gen_household_surveyreport(self, filename, location=None):
        story = []
        chws = None
        if location:
            try:
                chws = TheCHWReport.objects.filter(clinic=location)
            except TheCHWReport.DoesNotExist:
                raise BadValue(_(u"Unknown clinic: %(location)s specified." % \
                                    {'location': location}))
        if chws is None and  TheCHWReport.objects.all().count():
            chws = TheCHWReport.objects.all()

        for chw in chws:
            if not ThePatient.objects.filter(chw=chw, \
                                health_id=F('household__health_id')).count():
                continue
            patients = ThePatient.objects.filter(\
                    health_id=F('household__health_id'), chw=chw).\
                    order_by('location')
            tb = self.household_surveyreportable(_(u"Bednet Report - %(loc)s: %(chw)s" \
                                            % {'chw': chw, 'loc': chw.clinic.name}), \
                                            patients)
            story.append(tb)
            story.append(PageBreak())

            # 40 is the number of rows per page, should probably put this in a
            # variable
            if (((len(patients) / 47) + 1) % 2) == 1 \
                and not (len(patients) / 47) * 47 == len(patients):
                story.append(PageBreak())

        doc = SimpleDocTemplate(filename, pagesize=(8.5 * inch, 13.5 * inch), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch), showBoundary=0)
        doc.build(story)


    def household_surveyreportable(self, title, indata=None):
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        cols, subcol = ThePatient.mini_bednet_coverage()

        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        data = [hdata]

        thirdrow = ['#', RotatedParagraph(Paragraph(cols[0]['name'], styleH3), \
                                    1.3 * inch, 0.25 * inch)]
        thirdrow.extend([Paragraph(cols[1]['name'], styleN)])
        thirdrow.extend([Paragraph(cols[2]['name'], styleN)])
        thirdrow.extend([RotatedParagraph(Paragraph(col['name'], styleN), \
                                    1.3 * inch, 0.25 * inch) for col in cols[3:]])
        data.append(thirdrow)

        rowHeights = [None, 1.3 * inch]
        colWidths = [0.3 * inch, 0.6 * inch, 0.8 * inch, 2.0 * inch]
        colWidths.extend((len(cols) - 3) * [0.5 * inch])

        if indata:
            c = 0
            for row in indata:
                c = c + 1
                ctx = Context({"object": row})
                values = ["%d" % c, \
                            Paragraph(Template(cols[0]["bit"]).render(ctx), \
                            styleN)]
                values.extend([Paragraph(Template(col["bit"]).render(ctx), \
                                    styleN3) for col in cols[1:]])
                data.append(values)
            rowHeights.extend(len(indata) * [0.25 * inch])
        tb = ScaledTable(data, colWidths=colWidths, rowHeights=rowHeights, \
                repeatRows=2)
        tb.setStyle(TableStyle([('SPAN', (0, 0), (colWidths.__len__() - 1, 0)),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),
                                ('BOX', (4, 1), (9, -1), 5, \
                                colors.lightgrey)]))
        return tb

