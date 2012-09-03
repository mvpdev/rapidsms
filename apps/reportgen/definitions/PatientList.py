#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import copy

from django.utils.translation import ugettext as _
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

import bonjour.dates
from ccdoc.utils import register_fonts
from libreport.pdfreport import p
from libreport.pdfreport import MultiColDocTemplate

from childcount.models import Clinic
from childcount.models import CHW 
from childcount.models import Patient

from reportgen.PrintedReport import PrintedReport

styles = getSampleStyleSheet()

styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleH = styles['Heading1']
styleH.fontName = 'FreeSerif'
styleH3 = styles['Heading3']
styleH3.fontName = 'FreeSerif'


class ReportDefinition(PrintedReport):
    title = u'Patient List'
    filename = 'patient_list_'
    formats = ['pdf']
    variants = [(c.name, c.code+'_active', {'clinic_pk': c.pk}) \
        for c in Clinic.objects.all()]
   
    def register_columns(self):
        return (
            {'name': _(u"LOC"), \
            'bit':
                '{% if object.is_head_of_household %}<strong>' \
                '{{ object.household.location.code }}' \
                '</strong>{% endif %}',
            'width': 0.5 * inch},
            {'name': _(u"HID"), \
            'bit':
                '{% if object.is_head_of_household %}<strong>{% endif %}' \
                '{{object.health_id.upper}}' \
                '{% if object.is_head_of_household %}</strong>{% endif %}',
            'width': 0.5*inch},
            {'name': _(u"Name"), \
            'bit': "{{object.last_name}}{% if object.pk %},{% endif %} "
                    "{{object.first_name}}",
            'width': 1.7*inch},
            {'name': _(u"Gen."), \
            'bit': '{{object.gender}}',
            'width': 0.2*inch},
            {'name': _(u"Age"), \
            'bit': '{{object.humanised_age}}',
            'width': 0.9*inch})

    def generate(self, period, rformat, title, filepath, data):
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for patient list')

        self.set_progress(0.0)

        # Make sure that user passed in a clinic 
        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')
        clinic_pk = data['clinic_pk']

        # Produce the report
        f = open(filepath, 'w')

        register_fonts()
        self.gen_patient_register_pdf(f, period, clinic_pk)

        f.close()

    def gen_patient_register_pdf(self, f, period, clinic_pk):
        story = []
        clinic = Clinic.objects.get(pk=clinic_pk)
        chws = clinic.stationed_chw.all()

        if not chws.count():
            story.append(Paragraph(_("No report for %s.") % clinic, styleN))

        total = chws.count()
        for i,chw in enumerate(chws):
            self.set_progress(100.0*i/total)

            households = chw\
                .patient_set\
                .filter(pk=F('household__pk'))\
                .order_by('location__code','last_name')

            if not households:
                continue

            patients = []
            boxes = []
            last_loc = None
            for household in households:
                # Put blank line between cells
                if last_loc != None and last_loc != household.location.code:
                    patients.append(Patient())

                trow = len(patients)
                patients.append(household)
                hs = Patient\
                    .objects\
                    .filter(household=household, status=Patient.STATUS_ACTIVE)\
                    .exclude(health_id=household.health_id)\
                    .order_by('last_name')

                patients.extend(hs)

                last_loc = household.location.code
                brow = len(patients) - 1
                boxes.append({"top": trow, "bottom": brow})

            tb = self.thepatientregister(_(u"CHW: %(loc)s: %(chw)s") % \
                                    {'loc': clinic, 'chw': chw}, \
                                    patients, boxes)
            story.append(tb)
            story.append(PageBreak())

            # 108 is the number of rows per page, should probably put this in a
            # variable
            if (((len(patients) / 108) + 1) % 2) == 1 \
                and not (len(patients) / 108) * 108 == len(patients):
                story.append(PageBreak())

        story.insert(0, PageBreak())
        story.insert(0, PageBreak())
        story.insert(0, NextPageTemplate("laterPages"))
        doc = MultiColDocTemplate(f, 2, pagesize=A4, \
                                topMargin=(0.5 * inch), showBoundary=0)
        doc.build(story)
        return f

    
    def thepatientregister(self, title, indata=None, boxes=None):
        styleH3.alignment = TA_CENTER

        styleH5 = copy.copy(styleH3)
        styleH5.fontSize = 9
        styleH5.spaceAfter = 0
        styleH5.leading = 9
        styleH5.spaceBefore = 0

        styleN.fontSize = 9
        styleN.spaceAfter = 0
        styleN.leading = 9
        styleN.spaceBefore = 0
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        rpt = Patient()
        cols = self.register_columns()

        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        datedata = [Paragraph(_("Active Patients | Current as of ") + \
            bonjour.dates.format_date(format='long'), styleH5)]
        datedata.extend((len(cols) - 1) * [''])
        
        data = [hdata, datedata]

        firstrow = [Paragraph(cols[0]['name'], styleH5)]
        firstrow.extend([Paragraph(col['name'], styleH5) for col in cols[1:]])
        data.append(firstrow)

        rowHeights = [None, None, 0.2 * inch]
        # Loc, HID, Name
        colWidths = [col['width'] for col in cols]

        ts = [('SPAN', (0, 0), (len(cols) - 1, 0)),
                                ('SPAN', (0, 1), (len(cols)-1, 1)),
                                ('LINEABOVE', (0, 1), (len(cols) - 1, 1), 1, \
                                colors.black),
                                ('LINEBELOW', (0, 2), (len(cols) - 1, 2), 1, \
                                colors.black),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey)]
        if indata:
            for row in indata:
                ctx = Context({"object": row})
                values = [Paragraph(Template(cols[0]["bit"]).render(ctx), \
                                    styleN)]
                values.extend([Paragraph(Template(cols[1]["bit"]).render(ctx), \
                                    styleN)])
                values.extend([Paragraph(Template(cols[2]["bit"]).render(ctx), \
                                    styleN)])
                values.extend([Paragraph(Template(col["bit"]).render(ctx), \
                                    styleN2) for col in cols[3:]])
                data.append(values)
            rowHeights.extend(len(indata) * [0.2 * inch])

            tscount = 0
            for box in boxes:
                if tscount % 2:
                    ts.append((('BOX', (0, box['top'] + 3), \
                            (-1, box['bottom'] + 3), 0.5, colors.black)))
                else:
                    ts.append((('BOX', (0, box['top'] + 3), \
                            (-1, box['bottom'] + 3), 0.5, colors.black)))
                ts.append((('BACKGROUND', (0, box['top'] + 3), \
                            (2, box['top'] + 3), colors.lightgrey)))
                tscount += 1

        rowHeights = None
        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=3)
        tb.setStyle(TableStyle(ts))
        return tb

