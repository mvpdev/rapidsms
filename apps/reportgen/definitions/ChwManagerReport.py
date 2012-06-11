#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

import xlwt
from xlwt import XFStyle, Borders, Font, Style

from django.db.models.aggregates import Count
from django.utils.translation import ugettext as _
from django.template import Template, Context

from childcount.models import CHW
from childcount.models import Clinic
from childcount.models import Patient

from childcount import helpers 

from reportgen.utils import render_doc_to_file

from reportgen.PrintedReport import PrintedReport

class ReportDefinition(PrintedReport):
    title = _(u"CHW Manager Report")
    filename = 'chw_manager_report_'
    formats = ['xls']

    _safe_template = Template('{{value}}')
    _WIDTH_SKINNY = 0x0800

    _aggregate_on = []
    
    _LABEL_ROW = 1       # Indicator categories
    _SUB_LABEL_ROW = 2   # Indicator names
    _DATE_ROW = 3        # Time period labels
    _NAME_ROW = 2

    def _setup_styles(self):
        borders = Borders()
        borders.left = 20
        borders.right = 20
        self._spacer = XFStyle()
        self._spacer.borders = borders

        borders2 = Borders()
        borders2.right = 20
        self._end_section = XFStyle()
        self._end_section.borders = borders2
        
        self._end_section_perc = XFStyle()
        self._end_section_perc.borders = borders2
        self._end_section_perc.num_format_str = '0.0%'

        borders3 = Borders()
        borders3.bottom = 20
        borders3.right = 0
        bfont = Font()
        bfont.bold = True
        self._top_row = XFStyle()
        self._top_row.font = bfont
        self._top_row.alignment.horz = 2
        self._top_row.borders = borders3

        tfnt = Font()
        tfnt.height = 0xF0
        tfnt.bold = True
        self._section_row = XFStyle()
        self._section_row.font = tfnt
        self._section_row.alignment.horz = 1

        fnt = Font()
        fnt.height = 0x100
        fnt.bold = True
        self._title_style = XFStyle()
        self._title_style.font = fnt
        self._title_style.borders = borders3

        self._perc_style = XFStyle()
        self._perc_style.num_format_str = '0.0%'

        tbbords = Borders()
        tbbords.top = 30
        tbbords.bottom = 30
        self._total_style = XFStyle()
        self._total_style.borders = tbbords
        self._total_style.font = bfont
        self._total_style.alignment.horz = 3

        self._total_perc_style = XFStyle()
        self._total_perc_style.borders = tbbords
        self._total_perc_style.font = bfont
        self._total_perc_style.num_format_str = '0.0%'

    def generate(self, period, rformat, title, filepath, data):
        self._setup_styles()

        self._period = period
        self._sub_periods = period.sub_periods()
        self._numsp = len(self._sub_periods)
        self._indicators = helpers.chw.report_indicators()

        wb = xlwt.Workbook()
        self._ws = wb.add_sheet(_(u"Report"))
       
        clinics = Clinic\
            .objects\
            .annotate(c=Count('stationed_chw'))\
            .filter(c__gt=0)\
            .order_by('name')

        chws = CHW\
            .objects\
            .filter(is_active=True)\
            .exclude(clinic__isnull=True)\
            .order_by('clinic__name','first_name')

        # Write report titles
        self._write_merge(0, 0, 0, 1, self.title, self._title_style)
        self._write_merge(1, 1, 0, 1, period.title)

        self._ws.row(0).height = 0x180
        self._print_names(chws, clinics)

        self._print_header(self._indicators)


        total = chws.count() + clinics.count() + 1
        prog = 0

        row = self._DATE_ROW+1
        for (i,chw) in enumerate(chws):
            self.set_progress(100.0*prog/total)
            prog += 1
            
            self._print_data(row, chw.patient_set.all(), False)
            row += 1

        self._add_lines(row)

        # Write clinic totals
        row += 1
        for (i,clinic) in enumerate(clinics):
            self.set_progress(100.0*prog/total)
            prog += 1
            self._print_data(row, Patient.objects.filter(chw__clinic=clinic), True)
            row += 1

        self._add_lines(row)

        # Write MV totals
        row += 1
        self._print_data(row, Patient.objects.all(), True)
        self.set_progress(100.0*prog/total)

        wb.save(filepath)

    def _print_data(self, row, patient_set, is_totals):
        """Print one row of data, but do not
        print row labels
        """

        if is_totals:
            perc_style = self._total_perc_style 
            norm_style = self._total_style
            end_perc_style = self._total_perc_style 
            end_norm_style = self._total_style
        else:
            perc_style = self._perc_style
            norm_style = Style.default_style
            end_perc_style = self._end_section_perc
            end_norm_style = self._end_section


        col = 3
        for group in self._indicators:
            for ind in group['columns']:
                is_perc = ind['ind'].output_is_percentage()

                # Write value for each sub-period
                for sub_period in self._sub_periods:
                    value = ind['ind'](sub_period, patient_set)
                    if is_perc: value = float(value)

                    self._write(row, col, value, perc_style if is_perc\
                                        else norm_style)
                    col += 1

                # Write value for period as a whole
                value = ind['ind'](self._period, patient_set)
                if is_perc: value = float(value)

                self._write(row, col, value, end_perc_style if is_perc \
                                            else end_norm_style)
                col += 1
                    
            col += 1

    def _add_lines(self, row):
        """Print border lines between
        sections
        """
        col = 3
        for group in self._indicators:
            for ind in group['columns']:
                col += self._numsp
                self._write(row, col, "", self._end_section)
                col += 1
            col += 1

    def _add_spacer(self, col):
        """Add a spacer column
        """
        self._ws.col(col).width = 0x0100
        self._ws.col(col).set_style(self._spacer)

    def _print_header(self, indicators):
        """Print the header rows (indicator name,
        time period, etc)
        """
        col = 3
        for group in self._indicators:
            self._write_merge(self._LABEL_ROW, \
                self._LABEL_ROW, col, col+self._numsp, \
                "  " + group['title'], self._section_row)

            for pair in group['columns']:
                self._write_merge(self._SUB_LABEL_ROW, \
                    self._SUB_LABEL_ROW, col, col+self._numsp, \
                    pair['name'], self._top_row)

                for sp in self._sub_periods:
                    self._ws.col(col).width = self._WIDTH_SKINNY
                    self._write(self._DATE_ROW, col, sp.title)
                    col += 1

                self._write(self._DATE_ROW, 
                        col, 
                self._period.title,
                self._end_section)
                col += 1

            self._add_spacer(col)
            self._ws.col(col).set_style(self._end_section)
            self._ws.col(col).width = self._WIDTH_SKINNY
            col += 1

    def _print_names(self, chws, clinics):
        """Print the CHW and Clinic names
        down the left-hand side of the spreadsheet.
        """
        self._write(self._NAME_ROW, 0, _(u"CHW Name"), self._top_row)
        self._write(self._NAME_ROW, 1, _(u"Clinic"), self._top_row)

        for (i, chw) in enumerate(chws):
            self._write(i+self._DATE_ROW+1,0, chw.full_name())
            self._write(i+self._DATE_ROW+1,1, chw.clinic.code[0:2] if \
                chw.clinic else '--')

        row = self._NAME_ROW + chws.count() + 3
        for num, c in enumerate(clinics):
            self._write_merge(row+num, row+num, 0, 1, c.name,\
                self._total_style)
        row += clinics.count() + 1

        self._write_merge(row, row, 0, 1, _("Millennium Village"),\
                self._total_style)

        self._ws.col(0).width = 0x1800
        self._ws.col(1).width = self._WIDTH_SKINNY
        self._add_spacer(2)

    def _write(self, r, c, text, style=Style.default_style):
        print "Write %d %d %s" % (r,c,text)
        return self._ws.write(r, c, text, style)

    def _safe_value(self, text):
        return self._safe_template.render(\
            Context({'value': text}))

    def _write_merge(self, r1, r2, c1, c2, text, \
            style=Style.default_style):
        self._ws.write_merge(r1, r2, c1, c2, \
            self._safe_value(text), style)
        
