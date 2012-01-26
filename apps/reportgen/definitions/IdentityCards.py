#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import os
import copy

from django.utils.translation import ugettext as _
from django.template import Template, Context
from django.db.models import F

try:
    import Image
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.graphics.barcode import code128
except ImportError:
    pass

import bonjour.dates
from ccdoc.utils import register_fonts

from childcount.models import Clinic
from childcount.models import CHW 
from childcount.models import Patient

from reportgen.PrintedReport import PrintedReport

class ReportDefinition(PrintedReport):
    title = u'ID Cards'
    filename = 'id_cards_'
    formats = ['pdf']
    variants = [(c.name, c.code+'_active', {'clinic_pk': c.pk}) \
        for c in Clinic.objects.all()]
   
    def generate(self, period, rformat, title, filepath, data):
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for patient list')

        self.set_progress(0.0)

        # Make sure that user passed in a clinic 
        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')
        clinic_pk = data['clinic_pk']

        # Produce the report
        width, height = 3.5*inch, 2*inch
        register_fonts()
        c = canvas.Canvas(filepath, 
            pagesize=(width, height),\
            pageCompression=1)
        clinic = Clinic.objects.get(pk=clinic_pk)
        chws = clinic.stationed_chw.all()

        if not chws.count():
            self.add_error(c, width, height, _("No card for %s.") % clinic.name)

        total = Patient\
            .objects\
            .filter(chw__clinic__pk=clinic_pk,
                status=Patient.STATUS_ACTIVE)\
            .count()

        i=0
        for chw in chws:
            self.add_chw_header(c, width, height, chw)

            households = chw\
                .patient_set\
                .filter(pk=F('household__pk'))\
                .order_by('location__code','last_name')

            if not households:
                continue

            for household in households:
                hs = Patient\
                    .objects\
                    .filter(household=household)\
                    .order_by('last_name')\
                    .filter(status=Patient.STATUS_ACTIVE)

                for patient in hs:
                    self.add_card(c, width, height, patient)
                    i += 1
                    print (i, total)
                    self.set_progress(100.0*i/total)
        c.save()

    def add_error(self, canvas, width, height, s):
        canvas.setFont('FreeSerif', 0.25*inch)
        canvas.drawCentredString(width/2, height-0.4*inch, s)
        canvas.showPage()

    def add_chw_header(self, canvas, width, height, chw):
        canvas.setFont('FreeSerif', 0.15*inch)
        canvas.drawCentredString(width/2, height-0.4*inch, _("ID Cards for:"))
        canvas.setFont('FreeSerif', 0.25*inch)
        canvas.drawCentredString(width/2, height-0.7*inch, chw.full_name())
        canvas.setFont('FreeSerif', 0.15*inch)
        canvas.drawCentredString(width/2, height-1*inch, chw.clinic.name + u" / " + \
                    chw.clinic.code.upper())
        
        canvas.showPage()

    def add_card(self, canvas, width, height, patient):
        canvas.setFont('FreeSerif', 0.15*inch)
        canvas.drawCentredString(width/2, height-0.7*inch, _("Health ID Card"))
        canvas.setFont('FreeSerif', 0.3*inch)
        canvas.drawCentredString(width/2, height-1*inch, patient.full_name())
        canvas.drawRightString(width-0.1*inch, height-0.35*inch, patient.health_id.upper())
        barcode = code128.Code128(str(patient.health_id.upper()), \
            barWidth=0.01*inch, barHeight=0.5*inch)
        barcode.drawOn(canvas, 0.0, 0.1*inch)
        canvas.drawImage(os.path.join(os.path.dirname(__file__),\
                            '..','static','resources','MVP-Logo.png'),
            x=0.1*inch, 
            y=height-0.42*inch, 
            width=2*inch, 
            height=0.32*inch)
        canvas.setFont('FreeSerif', 0.15*inch)
        canvas.drawString(width-2*inch, 0.4*inch, \
            _("DOB: %s") % bonjour.dates.format_date(patient.dob, 'medium'))
        canvas.drawString(width-2*inch, 0.2*inch, \
            "%s / %s" % (patient.location.name, patient.location.code.upper()))
        canvas.drawCentredString(width/2, height-1.2*inch, \
            _("HH") + ": %s / %s" % (patient.household.full_name(), patient.household.health_id.upper()))
        canvas.showPage()
        
