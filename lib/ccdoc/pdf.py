#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

import os
import copy

from django import template

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, Paragraph, Frame, \
    BaseDocTemplate, PageBreak
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import PageTemplate, Spacer

from ccdoc.utils import register_fonts
from ccdoc.generator import Generator
from ccdoc.table import Table as cctable


# Load fonts
register_fonts()

TA_MAP = {
    cctable.ALIGN_LEFT: TA_LEFT,
    cctable.ALIGN_RIGHT: TA_RIGHT,
    cctable.ALIGN_CENTER: TA_CENTER,
    cctable.ALIGN_JUSTIFY: TA_JUSTIFY}


class SectionBreak(PageBreak):
    pass


class CustomDocTemplate(BaseDocTemplate):

    def afterFlowable(self, flowable):
        """ add another page break after a section end if on even page """

        if not self.stick_sections:
            return

        try:
            x = self.last_pb
        except AttributeError:
            self.last_pb = 0

        if isinstance(flowable, SectionBreak):
            page_num = self.canv.getPageNumber()
            # PB after even page requires new blank
            if (page_num % 2 == 0) and page_num - self.last_pb > 1 \
               and not page_num == 1:
                self.handle_pageBreak()
            self.last_pb = page_num


class PDFGenerator(Generator):

    def _start_document(self):
        self.PAGE_HEIGHT = 21.0 * cm
        self.PAGE_WIDTH = 29.7 * cm

        if self.landscape:
            x = self.PAGE_HEIGHT
            self.PAGE_HEIGHT = self.PAGE_WIDTH
            self.PAGE_WIDTH = x
            pagesize = landscape(A4)
        else:
            pagesize = A4

        self.text_templ = template.Template('{{text}}')

        self.styles = getSampleStyleSheet()

        self.styles['Normal'].fontName = 'FreeSerif'
        self.styles['Normal'].fontSize = 10

        ''' All Flowable elements on the page '''
        self.elements = []

        ''' Overall document object describing PDF '''

        # Conver to unicode
        if not isinstance(self.title, unicode):
            self.title = unicode(self.title)
        self.doc = CustomDocTemplate(self._filename,
            showBoundary=0, pagesize=pagesize,
            title = self.title)

        self.doc.stick_sections = self.stick_sections

        ''' Frame template defining page size, margins, etc '''
        self.tframe = Frame(1.5 * cm, 1.5 * cm,
                        self.PAGE_HEIGHT - 3 * cm, self.PAGE_WIDTH - 3 * cm,
                       showBoundary=0, topPadding=0, bottomPadding=0,
                       rightPadding=0, leftPadding=0)

        self.section_style = copy.copy(self.styles['Normal'])
        self.section_style.fontSize = 18
        print self.section_style.fontName
        self.section_style.leading = 20
        self.section_style.spaceBefore = 1 * cm

        ''' Table style '''
        self.table_style = copy.copy(self.styles['Normal'])
        self.table_style.fontSize = 9
        self.table_style.leading = 10
        self.table_style.alignment = 1

        ''' Document title '''
        title_style = copy.copy(self.styles['Normal'])
        title_style.fontSize = 24
        title_style.leading = 28
        self.elements.append(Paragraph(unicode(self.title), title_style))

        ''' Date string '''
        date_style = copy.copy(self.styles['Normal'])
        date_style.fontSize = 10
        date_style.leading = 13
        if not isinstance(self.datestring, unicode):
            self.datestring = unicode(self.datestring)
        self.elements.append(Paragraph(self.datestring, date_style))

        ''' Subtitle '''
        if self.subtitle != None and self.subtitle != '':
            subtitle_style = copy.copy(self.styles['Normal'])
            subtitle_style.fontSize = 16
            subtitle_style.leading = 18
            subtitle_style.spaceAfter = 0.5 * cm
            if not isinstance(self.subtitle, unicode):
                self.subtitle = unicode(self.subtitle)
            self.elements.append(Paragraph(self.subtitle, subtitle_style))

    def _render_section(self, section):
        if not isinstance(section.text, unicode):
            section.text = unicode(section.text)

        element = Paragraph(
                u'<strong>' + section.text + u'</strong>',
                self.section_style)
        if self.stick_sections:
            # on printer stick mode
            # we add a blank page before new section
            self.elements.append(SectionBreak())
        self.elements.append(element)

    def _render_pagebreak(self, pagebreak):
        self.elements.append(PageBreak())

    def _render_text(self, text):
        output = u''
        if text.bold:
            output += "<strong>"
        if text.italic:
            output += "<i>"
        if text.size != text.DEFAULT_SIZE:
            output += "<font size=%d>" % text.size

        datext = text.text
        try:
            datext = unicode(datext)
        except:
            pass

        c = template.Context({'text': datext})

        '''
            Render using Django templates to avoid
            issues with special characters, escapes, etc, etc
        '''
        output += self.text_templ.render(c)

        if text.size != text.DEFAULT_SIZE:
            output += "</font>"
        if text.italic:
            output += "</i>"
        if text.bold:
            output += "</strong>"
        return output

    def _render_paragraph(self, paragraph):
        textout = u''
        for p in paragraph.contents:
            textout += self._render_text(p)

        self.elements.append(Spacer(0.5 * cm, 0.5 * cm))
        self.elements.append(Paragraph(textout, self.styles['Normal']))

    def _render_hline(self, hline):
        self.elements.append(Spacer(1 * cm, 1 * cm))

    def _render_table(self, table):
        tabdata = []
        tabstyle = []

        i = 1 
        j = 1
        if table.title != None:
            title_row = [u''] * table.ncols

            title_style = copy.copy(self.styles['Normal'])
            title_style.alignment = 1 # Align center
            title_style.fontSize = 14
            title_style.leading = 16

            title_row[0] = Paragraph(self._render_text(table.title), title_style)

            tabdata.append(title_row)
            tabstyle.append(('SPAN', (0, 0), (-1, 0)))
            tabstyle.append(('GRID', (0, 1), (-1, -1), 0.25, colors.black))
            tabstyle.append(('BOTTOMPADDING', (0, 0), (0, 0), 6))
            i += 1

        ''' Iterate through each table row '''
        for row in table.rows:
            rowdata = []

            # row[0] is true when this is a header row
            k = 0
            for c in row[1]:
                if row[0]:
                    j = 1
                    c.bold = True
                    tabstyle.append(('LINEBELOW', (0, i-1), (-1, i-1), 0.5,
                                        colors.black))
                # Paragraph style is dynamic
                rowdata.append(Paragraph(self._render_text(c), \
                                          self.get_row_style(table, column=k)))
                k += 1
            tabdata.append(rowdata)

            # Zebra stripes (not on header rows)
            if j % 2 == 1:
                tabstyle.append(('BACKGROUND', \
                    (0, i), (-1, i), \
                    colors.HexColor('#eeeeee')))

            i += 1
            j += 1

        ''' Align all in middle '''
        tabstyle.append(('LEFTPADDING', (0, 0), (-1, -1), 1))
        tabstyle.append(('RIGHTPADDING', (0, 0), (-1, -1), 1))
        tabstyle.append(('TOPPADDING', (0, 0), (-1, -1), 1))
        tabstyle.append(('BOTTOMPADDING', (0, 0), (-1, -1), 2))

        table = Table(tabdata, style=tabstyle, \
                      colWidths=self.gen_column_widths(table),  repeatRows=1)
        self.elements.append(table)

    def get_row_style(self, table, column):
        """ return a Style object based on a column number

        serves either the standard table_style or same with custom alignment
        if it's been modified """

        if column in table.column_alignments:
            custom_style = copy.copy(self.table_style)
            custom_style.alignment = TA_MAP[table.column_alignments[column]]
            return custom_style
        return self.table_style

    def gen_column_widths(self, table):
        """ returns a colWidths compatible list of widths for all columns

        sizes are calculated from user requests """

        # total available width
        total_width = self.PAGE_HEIGHT - 3 * cm
        # static
        auto = 'auto'
        # available width used for counting
        avail = total_width
        # number of columns set
        set_columns = 0

        widths = {}
        for col in range(0, table.ncols + 1):
            if col in table.column_widths:
                widths[col] = (table.column_widths[col] * total_width) / 100.0
                avail -= widths[col]
                set_columns += 1
            else:
                widths[col] = auto
        default_width = float(avail) / (table.ncols - set_columns)
        for col in range(0, table.ncols + 1):
            if widths[col] == auto:
                widths[col] = default_width

        return widths.values()

    def _end_document(self):
        template = PageTemplate('normal', [self.tframe])
        self.doc.addPageTemplates(template)

        self.doc.build(self.elements)
