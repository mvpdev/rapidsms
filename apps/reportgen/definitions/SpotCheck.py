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
from childcount.models import Encounter
import childcount.helpers

from childcount.utils import RotatedParagraph

from libreport.pdfreport import p

import bonjour.dates

from ccdoc.utils import register_fonts
from reportgen.PrintedReport import PrintedReport
from reportgen.utils import render_doc_to_file

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleN.fontName = 'FreeSerif'
styleN.fontSize = 10

styleH3 = styles['Heading3']
styleH3.fontName = 'FreeSerif'
styleH3.fontSize = 12

styleH3r = copy.copy(styles['Heading3'])
styleH3r.fontName = 'FreeSerif'
styleH3r.fontSize = 12
styleH3r.alignment = TA_RIGHT

styleH1 = styles['Heading1']
styleH1.fontSize = 14
styleH1.fontName = 'FreeSerif'

class ReportDefinition(PrintedReport):
    title = 'Spot Check'
    filename = 'spot_check_'
    formats = ('pdf',)

    variants = [(c.name, c.code, {'clinic_pk': c.pk}) \
                                    for c in Clinic.objects.all()]

    form_codes = ['V', 'K', 'U', 'S', 'P', 'N', 'T', 'M', 'F', 'G', 'R',]
    totals = {}

    def generate(self, period, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF '\
                                        'for spot check report')

        self.period = period
        self.set_progress(0.0)

        story = []

        # Datestamp
        story.append(Paragraph(u"<b>%(name)s - %(title)s</b>" % \
                {'name': title,\
                'title': period.title}, styleH1))

        story.append(Paragraph(_('(Generated on %(gen_datetime)s)') % \
                {'gen_datetime': \
                    bonjour.dates.format_datetime(format='medium')}, styleN))

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

        story.append(PageBreak())
        for c in chws:
            for code in self.form_codes:
                self.totals[code] = 0

            story.append(self._spot_check_table(period, c))
            story.append(self._totals_table(period, c))
            story.append(Paragraph("<br><br>", styleN))
            story.append(PageBreak())

        register_fonts()
        f = open(filepath, 'w')
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0.4 * inch), \
                                bottomMargin=(0.4 * inch),\
                                leftMargin=(0.4 *inch),\
                                rightMargin=(0.4*inch))
        doc.build(story)
        f.close()
    
    def _patient_encounter_summary(self, patient):
        hhv = childcount\
            .helpers\
            .patient\
            .latest_hhv_raw(self.period, patient.household)
        if hhv is None:
            return u""

        hhv_date = hhv.encounter.encounter_date
        enc = self._encounter_for_patient(patient, hhv_date.year, hhv_date.month, hhv_date.day)
        
        ccrpts = enc.ccreport_set.all()
        furs = ccrpts\
            .filter(polymorphic_ctype__name='Follow-up Report')
        dss = ccrpts\
            .filter(polymorphic_ctype__name='Danger Signs Report')
        pregs = ccrpts\
            .filter(polymorphic_ctype__name='Pregnancy Report')
        neos = ccrpts\
            .filter(polymorphic_ctype__name='Neonatal Report')
        u1s = ccrpts\
            .filter(polymorphic_ctype__name='Under One Report')
        nuts = ccrpts\
            .filter(polymorphic_ctype__name='Nutrition Report')
        fevs = ccrpts\
            .filter(polymorphic_ctype__name='Fever Report')
        meds = ccrpts\
            .filter(polymorphic_ctype__name='Medicine Given Report')
        refs = ccrpts\
            .filter(polymorphic_ctype__name='Referral Report')

        out = u""
        if furs.count():
            fur = furs[0]
            out += _("<b>+U</b>") + " " + fur.improvement + " " + fur.visited_clinic + " "
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["U"] += 1
        if dss.count():
            ds = dss[0]
            out += _("<b>+S</b>") + " "
            out += " ".join([s.local_code.upper() for s in ds.danger_signs.all()])
            out += " "
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["S"] += 1
        if pregs.count():
            preg = pregs[0]
            out += _("<b>+P</b>") + " %d %d " % (preg.pregnancy_month, preg.anc_visits)
            if preg.anc_visits:
                out += "%d " % preg.weeks_since_anc
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["P"] += 1
        if neos.count():
            neo = neos[0]
            out += _("<b>+N</b>") + " %d " % neo.clinic_visits
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["N"] += 1
        if u1s.count():
            u1 = u1s[0]
            out += _("<b>+T</b>")
            out += " %s %s " % (u1.breast_only, u1.immunized)
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["T"] += 1
        if nuts.count():
            nut = nuts[0]
            out += _("<b>+M</b>") + " "
            if nut.muac:
                out += "%d " % nut.muac
            else:
                out += "0 "
            out += nut.oedema + " "
            if nut.weight:
                out += "%f " % nut.weight
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["M"] += 1
        if fevs.count():
            fev = fevs[0]
            out += _("<b>+F</b>") + " %s " % fev.rdt_result
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["F"] += 1
        if meds.count():
            med = meds[0]
            out += _("<b>+G</b>") + " "
            out += " ".join([m.local_code.upper() for m in med.medicines.all()])
            out += " "
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["G"] += 1
        if refs.count():
            ref = refs[0]
            out += _("<b>+R</b>") + " %s " % ref.urgency
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals["R"] += 1

        return out

    def _hh_encounter_summary(self, patient):
        master = childcount.helpers.patient.latest_hhv_raw(self.period, patient)
        if master is None:
            return _("[No HHV]")

        ccrpts = master.encounter.ccreport_set.all()
        hhvs = ccrpts.filter(polymorphic_ctype__name='Household Visit Report')
        fps = ccrpts.filter(polymorphic_ctype__name='Family Planning Report')

        out = u""
        if hhvs.count():
            hhv = hhvs[0]
            out += _("<b>+V</b> ")
            out += "Y" if hhv.available else "N"
            out += " "
            out += unicode(hhv.children) if hhv.available else ""
            out += " "
            out += childcount.helpers.patient.latest_hhv_counseling(self.period, patient)
            out += "&nbsp;&nbsp;&nbsp;"
            self.totals['V'] += 1

        if fps.count():
            fp = fps[0]
            out += _(" <b>+K</b> ")
            out += "%d " % (fp.women or 0)
            out += "%d " % (fp.women_using or 0)
            out += "      "
            self.totals['K'] += 1

        return out

    def _encounter_for_patient(self, patient, year, month, day):
        es = Encounter\
                .objects\
                .filter(patient=patient,
                    encounter_date__year=year,
                    encounter_date__month=month,
                    encounter_date__day=day)
        if not es.count():
            return None

        return es[0]
    def _spot_check_columns(self):
        return [
            {
                'name': _("Date HH Visited\n<em>(DDMMYY)</em>"),
                'width': 0.28 * inch,
            },
            { 
                'name': "", 
                'width': 0.28 * inch,
                'lineafter': True,
            },
            { 
                'name': "", 
                'width': 0.28 * inch,
            },
            { 
                'name': "", 
                'width': 0.28 * inch,
                'lineafter': True,
            },
            { 
                'name': "", 
                'width': 0.28 * inch,
            },
            { 
                'name': "", 
                'width': 0.28 * inch,
                'lineafter': True,
            },
            {
                'name': _(u"Avail.\n(Y-N)"),
                'width': 0.55 * inch,
                'lineafter': True,
            },
            {
                'name': _("Loc."),
                'value': lambda p: p.location.code.upper(),
                'width': 0.55 * inch,
            },
            {
                'name': _("Last HH Visit"),
                'value': lambda p: \
                    childcount.helpers.patient.latest_hhv_date(self.period, p),
                'width': 1*inch,
            },
            {
                'name': _("HID"),
                'value': lambda p: p.household.health_id.upper(),
                'valuep': lambda p: p.health_id.upper(),
                'width': 0.6 * inch,
            },
            {
                'name': _("Patient"),
                'value': lambda p: ("<b>%s</b>" % p.full_name()) + \
                            " " + p.gender + "/" + p.humanised_age(),
                'valuep': lambda p: p.full_name() + \
                            " " + p.gender + "/" + p.humanised_age(),
            },
            {
                'name': _("Visit Summary"),
                'value': self._hh_encounter_summary,
                'valuep': self._patient_encounter_summary,
                'lineafter': True,
            },
            {
                'name': _("Notes"),
                'lineafter': True,
            },
        ]

    def _totals_table(self, period, chw):

        table = []
        table.append([""] + ["+%s" % c for c in self.form_codes] + \
            [Paragraph(_("<b>Total</b>"), styleN)])
        table.append([_("OK")] + ["" for c in self.form_codes] + [""])
        table.append([_("Not Available")] + ["" for c in self.form_codes] + [""])
        table.append([_("Bad")] + ["" for c in self.form_codes] + [""])
        table.append([_("Total")] + \
            ["%d" % self.totals[c] for c in self.form_codes] + \
            [Paragraph("<b>%d</b>" % \
                sum([self.totals[c] for c in self.form_codes]), styleN)])

        style = [('GRID', (0,0), (-1,-1), 0.3, colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT')]

        for i,c in enumerate(self.form_codes):
            if not self.totals[c]:
                style.append(('BACKGROUND', (i+1, 0), (i+1, -1), colors.lightgrey))

        colWidths = [1*inch] + ([None]*len(self.form_codes)) + [0.5*inch]
        tot_table = Table(table, style=style, colWidths=colWidths)

        table2 = []
        for i in xrange(0, 6):
            table2.append([Paragraph("_"*60, styleH3)])
        comment_table = Table(table2)

        big_table = [["",""]]
        big_table.append([Paragraph(_("General Comments:"), styleH3),\
                        Paragraph(_("Overall Performance:"), styleH3)])
        big_table.append([comment_table, tot_table])

        return Table(big_table, style = [('SPAN', (1, 2), (1, -1)),
                                            ('VALIGN', (0,0), (-1,-1), 'TOP')])

    def _spot_check_table(self, period, chw):
        cols = self._spot_check_columns()
        ncols = len(cols)
       
        row_name = [[]]*ncols
        row_name[0] = [\
            Paragraph("<b>%s - %s</b>" % \
                (chw.full_name(), chw.clinic.name) , styleH3),
            Paragraph(_('Generated on %(gen_datetime)s') % \
                    {'gen_datetime': \
                        bonjour.dates.format_datetime(format='full')}, styleN)]
        row_name[-3] = Paragraph(_("Prepared By: ___________________________ " \
                                    "Submitted On: _____/_____/_________") , styleH3r)

        row_labels = [Paragraph(c['name'], styleN) for c in cols]
       
        patients = Patient\
            .objects\
            .filter(encounter__encounter_date__range=(period.start, period.end),
                chw=chw)\
            .household(period.start, period.end)\
            .order_by('?')[0:5]

        patients = sorted(patients, key=lambda p: p.location.code)

        table = [row_name, row_labels]
        style = []

        index = 1
        for hh in patients: 
            for i,c in enumerate(cols): 
                if c.get('lineafter'):
                    style.append(('LINEAFTER', (i, index+1), (i, index+1), 1.25, colors.black))

            style.append(('GRID', (0, index+1), (-1, index+1), 0.3, colors.black))
            style.append(('LINEBELOW', (0, index), (-1, index), 1, colors.black))

            row = [[]]*ncols
            for i,c in enumerate(cols):
                if 'value' in c:
                    row[i] = Paragraph(c['value'](hh), styleN)
            table.append(row)
            
            hhv = childcount\
                .helpers\
                .patient\
                .latest_hhv_raw(self.period, hh)
            if hhv is None:
                continue

            hhv_date = hhv.encounter.encounter_date
            for p in hh.household_member.exclude(pk=hh.pk):
                e = self._encounter_for_patient(p, hhv_date.year, hhv_date.month, hhv_date.day)
                if not e: 
                    continue

                row = [[]]*ncols
                for i,c in enumerate(cols):
                    if 'valuep' in c:
                        row[i] = Paragraph(c['valuep'](p), styleN)
                table.append(row)
                index += 1
            index += 1

        if len(table) == 2:
            table.append([Paragraph(_("<b>CHW made no household visits during "\
                                    "this time period.</b>"), styleH3)] \
                + [[]] * (ncols-1))
            style.append(("SPAN", (0,2), (-1, 2)))
        colWidths = [c['width'] if 'width' in c else None for c in cols] 
        style.extend([#('GRID', (0,1), (-1,-1), 0.3, colors.black),
                    ('SPAN', (0,0), (-4,0)),
                    ('SPAN', (1,0), (4,0)),
                    ('LINEBELOW', (0, -1), (-1, -1), 1.25, colors.black),
                    ('LINEBELOW', (0, 1), (-1, 1), 1.25, colors.black),
                    ('SPAN', (0,1), (5,1)),
                    ('GRID', (0, 1), (-1, 1), 0.3, colors.black),
                    ('GRID', (9, 1), (-1, -1), 0.3, colors.black),
                    ('LINEBEFORE', (0, 2), (0, -1), 1.25, colors.black),
                    ('BOX', (-1, 2), (-1, -1), 1.25, colors.black),
                    ('SPAN', (-3,0), (-1,0))])

        return Table(table, colWidths=colWidths, style=style)
