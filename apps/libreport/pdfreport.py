#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os
from datetime import datetime
import copy

from django.template import Template, Context
from django.http import HttpResponse

try:
    from reportlab.platypus.flowables import Flowable
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import BaseDocTemplate, PageTemplate, \
        Paragraph, PageBreak, Frame, FrameBreak, NextPageTemplate, Spacer, \
        Preformatted
    from reportlab.platypus import Table as PDFTable
    from reportlab.platypus import TableStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.rl_config import defaultPageSize
    from reportlab.lib.units import inch
    PAGE_HEIGHT = defaultPageSize[1]
    PAGE_WIDTH = defaultPageSize[0]
except ImportError:
    pass

styles = getSampleStyleSheet()
HeaderStyle = styles["Heading1"]


def pheader(txt, style=HeaderStyle, klass=Paragraph, sep=0.3):
    '''Creates a reportlab PDF element and adds it to the global Elements list

    style - can be a HeaderStyle, a ParaStyle or a custom style,
     default HeaderStyle
    klass - the reportlab Class to be called, default Paragraph
    sep    - space separator height
    '''
    elements = []
    s = Spacer(0.2 * inch, sep * inch)
    elements.append(s)
    para = klass(txt, style)
    elements.append(para)
    return elements

#Paragraph Style
ParaStyle = styles["Normal"]


def p(txt):
    '''Create a text Paragraph using  ParaStyle'''
    return pheader(txt, style=ParaStyle, sep=0.0)

#Preformatted Style
PreStyle = styles["Code"]


def pre(txt):
    '''Create a text Preformatted Paragraph using  PreStyle'''
    elements = []
    s = Spacer(0.1 * inch, 0.1 * inch)
    elements.append(s)
    p = Preformatted(txt, PreStyle)
    elements.append(p)
    return elements


class PDFReport():

    '''PDFReport

    PDFReport Is a class that create table format reports
    The Title is placed on its own page for the first page
    usage:
            pdfrpt = PDFRrepot()
            pdfrpt.setLandscape(False)
            pdfrpt.setTitle("Title")
            pdfrpt.setTableData(queryset, fields, "Table Title")
            pdfrpt.setFilename("filename")
            pdfrpt.setNumOfColumns(2) # for two column setup
            pdfrpt.render()
    '''
    title = u"Report"
    pageinfo = ""
    filename = "report"
    styles = getSampleStyleSheet()
    table_style = None
    data = []
    landscape = False
    hasfooter = False
    headers = []
    cols = 1
    PAGESIZE = A4
    fontSize = 8
    rowsperpage = 90
    print_on_both_sides = False
    firstRowHeight = 0.25
    rotateTextFirstRow = False

    def __init__(self):
        self.headers.append("")

    def setPrintOnBothSides(self, state):
        ''' enable or disable landscape display

            @var state: True or False
        '''
        self.print_on_both_sides = state

    def setLandscape(self, state):
        ''' enable or disable landscape display

            @var state: True or False
        '''
        self.landscape = state

    def setRowsPerPage(self, num):
        ''' Sets the number of rows per page for Table data

            @var num: int
        '''
        self.rowsperpage = int(num)

    def enableFooter(self, state):
        '''     enable formatter for the last row of the table
        e.g for summaries have bold border lines

        @var state: True or False
        '''
        self.hasfooter = state

    def setTitle(self, title):
        ''' @var title: The Report Title '''
        if title:
            self.title = title

    def setPageInfo(self, pageinfo):
        if pageinfo:
            self.pageinfo = pageinfo

    def setFilename(self, filename):
        ''' @var filename: filename for the generated pdf document '''
        if filename:
            self.filename = filename

    def setFontSize(self, size):
        ''' @var size: font-size '''
        if size:
            self.fontSize = size

    def setNumOfColumns(self, cols):
        ''' @var cols: number of columns '''
        if cols:
            self.cols = cols

    def setPageBreak(self):
        ''' force/add a page break '''
        self.data.append(PageBreak())

    def setElements(self, elements):
        ''' Add elements like paragraphs to the overall data '''
        for i in elements:
            self.data.append(i)

    def setTableStyle(self, ts):
        self.table_style = ts

    def getTableStyle(self):
        if self.table_style:
            return self.table_style
        ts = [
              ('ALIGNMENT', (0, 1), (-1, -1), 'LEFT'),
              ('LINEBELOW', (0, 0), (-1, -0), 2, colors.black),
              ('GRID', (0, 0), (-1, -0), 0.25, colors.black),
              ('LINEBELOW', (0, 1), (-1, -1), 0.8, \
                                            colors.lightgrey),
              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
              ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
              ('TOPPADDING', (0, 0), (-1, -1), 2), ('ROWBACKGROUNDS', \
                                                (0, 1), (-1, -1), \
             [colors.whitesmoke, colors.white]),
            ('FONT', (0, 0), (-1, -1), "Times-Roman", self.fontSize)]

        #last row formatting when required
        if self.hasfooter is True:
            ts.append(('LINEABOVE', (0, -1), (-1, -1), 1, colors.black))
            ts.append(('LINEBELOW', (0, -1), (-1, -1), 2, colors.black))
            ts.append(('LINEBELOW', (0, 3), (-0, -0), 2, colors.green))
            ts.append(('LINEBELOW', (0, -1), (-1, -1), 0.8, \
                       colors.lightgrey))
            ts.append(('FONT', (0, -1), (-1, -1), "Times-Roman", 7))
        return ts

    def setFirstRowHeight(self, height):
        '''Set the height of the first row'''
        self.firstRowHeight = height

    def getFirstRowHeight(self):
        return  self.firstRowHeight

    def getRowHeights(self, numOfRows):
        '''retuns the row heights'''
        rh = [self.getFirstRowHeight() * inch]
        numOfRows -= 1
        rh.extend(numOfRows * [0.25 * inch])
        return rh

    def rotateText(self, bl):
        self.rotateTextFirstRow = bl

    def setTableData(self, queryset, fields, title, colWidths=None, \
                                                            hasCounter=False):
        '''set table data

        @var queryset: data
        @var fields: table column headings
        @var title: Table Heading
        '''
        data = []
        header = False
        c = 0
        pStyle = copy.copy(self.styles["Normal"])
        pStyle.fontName = "Times-Roman"
        pStyle.fontSize = 7
        pStyle.spaceBefore = 0
        pStyle.spaceAfter = 0
        pStyle.leading = pStyle.fontSize + 2.8
        hStyle = copy.copy(self.styles["Normal"])
        #hStyle.fontName = "Arial Narrow-Bold"
        hStyle.fontSize = 8
        hStyle.alignment = TA_CENTER
        #hStyle.spaceBefore = 0
        hStyle.spaceAfter = 0
        #pStyle.leading = pStyle.fontSize + 2.8
        #prepare the data
        counter = 0
        for row in queryset:
            counter += 1
            if not header:
                if self.rotateTextFirstRow:
                    hStyle.borderWidth = 0
                    hStyle.alignment = TA_LEFT
                    hStyle.borderPadding = 5
                    value = [RotatedParagraph( Paragraph('<b>' + f["name"] + \
                                                    '</b>', hStyle), \
                                            self.getFirstRowHeight() * inch, \
                                            0.25 * inch) \
                                            for f in fields]
                else:
                    value = [pheader(f["name"], hStyle, sep=0) for f in fields]
                if hasCounter:
                    value.insert(0, '#')
                data.append(value)
                header = True
            ctx = Context({"object": row})

            values = [pheader(Template(h["bit"]).render(ctx), pStyle, sep=0)\
                       for h in fields]
            if hasCounter:
                values.insert(0, counter)

            data.append(values)

        if len(data):
            ts = self.getTableStyle()

            table = PDFTable(data, colWidths, self.getRowHeights(len(data)), \
                                style=ts, splitByRow=1)

            table.hAlign = "LEFT"
            self.data.append(table)
        else:
            self.data.append(Paragraph("No Report", self.styles['Normal']))
        '''The number of rows per page for two columns is about 90.
            using this information you can figure how many pages the
            table is going to overlap hence you place a header/subtitle
            in that position for it to be printed appropriately
        '''
        c = float(len(queryset)) / self.rowsperpage

        needsSecondPage = True
        if int(c) < c:
            c = int(c) + 1
            needsSecondPage = False
        if int(c) == 0:
            c = 1
        if self.print_on_both_sides is True:
            if int(c) == 1 or (int(c) % 2) == 1:
                #take care of headings, do not displace them
                c = int(c) + 1
                needsSecondPage = True
                self.data.append(PageBreak())

        for i in range(int(c)):
            if self.print_on_both_sides is True and needsSecondPage is True \
                and i == (int(c) - 1):
                #empty title to allow blank page
                title = ""
            self.headers.append(title)
        #exit((needsSecondPage, c, self.headers, title, i))

    def render(self):
        elements = []

        self.styles['Title'].alignment = TA_LEFT
        self.styles['Title'].fontName = self.styles['Heading2'].fontName = \
            "Times-Roman"
        self.styles["Normal"].fontName = "Times-Roman"
        self.styles["Normal"].fontSize = 7
        #self.styles["Normal"].fontWeight = "BOLD"

        filename = self.filename + \
            datetime.now().strftime("%Y%m%d%H%M%S") + ".pdf"
        #doc = SimpleDocTemplate(filename)

        #now create the title page
        elements.append(Paragraph(self.title, self.styles['Title']))

        if self.print_on_both_sides is True:
            elements.append(PageBreak())
            self.headers.insert(1, "")
        #done with the title info, move to the next frame
        #and queue up the later page template
        elements.append(FrameBreak())
        elements.append(NextPageTemplate("laterPages"))
        elements.append(PageBreak())
        #exit(self.headers)
        for data in self.data:
            elements.append(data)

        if self.landscape is True:
            self.PAGESIZE = landscape(A4)
        doc = MultiColDocTemplate(filename, self.cols, \
                        pagesize=self.PAGESIZE, allowSplitting=1, \
                            showBoundary=0)
        doc.setTitle(self.title)
        doc.setHeaders(self.headers)
        doc.build(elements)

        response = HttpResponse(mimetype='application/pdf')
        response['Cache-Control'] = ""
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        response.write(open(filename).read())
        os.remove(filename)
        return response

    # what should appear on the first page
    def myFirstPage(self, canvas, doc):
        pageinfo = self.pageinfo
        canvas.saveState()
        '''canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" %
         (doc.page, pageinfo))
        '''
        textobject = canvas.beginText()
        textobject.setTextOrigin(inch, 0.75 * inch)
        textobject.setFont("Times-Roman", 9)
        textobject.textLine("Page %d" % (doc.page))
        textobject.setFillGray(0.4)
        textobject.textLines(pageinfo)
        canvas.hAlign = "CENTER"
        canvas.drawText(textobject)
        canvas.restoreState()

    # what to do on other pages
    def myLaterPages(self, canvas, doc):
        pageinfo = self.pageinfo
        canvas.saveState()
        '''canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s"
        % (doc.page, pageinfo))
        '''
        textobject = canvas.beginText()
        textobject.setTextOrigin(inch, 0.75 * inch)
        textobject.setFont("Times-Roman", 9)
        textobject.textLine("Page %d" % (doc.page))
        textobject.setFillGray(0.4)
        textobject.textLines(pageinfo)
        canvas.hAlign = "CENTER"


class MultiColDocTemplate(BaseDocTemplate):

    '''A multi column document template'''

    headers = []
    title = u"Report Title Here"

    def __init__(self, filename, frameCount=1, **kw):
        '''@FIXME: need to remove frameCount to maintain consistency
         with BaseDocTemplate constructor
                   and hence find a way to pass frameCount
        '''
        apply(BaseDocTemplate.__init__, (self, filename), kw)
        self.addPageTemplates(self.firstPage())

        frameWidth = (self.width / frameCount) + .85 * inch
        frameHeight = self.height - .5 * inch
        frames = []

        for frame in range(frameCount):
            leftMargin = self.leftMargin + frame * frameWidth - .85 * inch
            column = Frame(leftMargin, self.bottomMargin - .95 * inch, \
                    frameWidth, frameHeight + 1.75 * inch, leftPadding=1, \
                    topPadding=1, rightPadding=1, bottomPadding=1)
            frames.append(column)

        template = PageTemplate(frames=frames, id="laterPages", \
                                onPage=self.addHeader)
        self.addPageTemplates(template)

    def firstPage(self):
        style = getSampleStyleSheet()
        #title page styles
        titleStyle = style["Title"]
        titleStyle.fontSize = 40
        titleStyle.leading = titleStyle.fontSize * 1.1
        #need to copy the object or style changes will
        # apply to any incarnation of "Normal"
        subTitleStyle = copy.copy(style["Normal"])
        subTitleStyle.alignment = TA_CENTER
        subTitleStyle.fontName = "Times-Roman"

        frameHeight = self.height - .5 * inch
        frameWidth = self.width
        #title page frames
        firstPageHeight = 3.5 * inch
        firstPageBottom = frameHeight - firstPageHeight
        framesFirstPage = []
        titleFrame = Frame(self.leftMargin, firstPageBottom, self.width, \
                           firstPageHeight)
        framesFirstPage.append(titleFrame)
        #columns for the first page
        firstPageColumn = Frame(self.leftMargin, self.bottomMargin, \
                                frameWidth, firstPageBottom)
        framesFirstPage.append(firstPageColumn)
        return PageTemplate(frames=framesFirstPage, id="firstPage")

    def addHeader(self, canvas, document):
        ''' display the heading of the page or document '''
        canvas.saveState()
        title = self.getSubTitle(document.page - 1)
        fontsize = 12
        fontname = 'Times-Roman'
        headerBottom = document.bottomMargin + document.height + \
                document.topMargin / 2
        bottomLine = headerBottom - fontsize / 4
        topLine = headerBottom + fontsize
        lineLength = document.width + document.leftMargin
        canvas.setFont(fontname, fontsize)

        canvas.drawString(document.leftMargin, headerBottom, title)
        canvas.restoreState()

    def getTitle(self):
        return u"%s" % self.title

    def setTitle(self, title):
        if title:
            self.title = title

    def getSubTitle(self, pos):
        try:
            ''' since subtitles vary from page to page, I pick the relevant
             title according to the page number '''
            return u"%s" % self.headers[pos]
        except:
            return u""

    def setHeaders(self, headers):
        self.headers = headers


class RotatedText(Flowable):

    '''Rotates text in a table cell.'''

    def __init__(self, text ):
        Flowable.__init__(self)
        self.text=text

    def draw(self):
        canv = self.canv
        canv.rotate(90)
        canv.drawString( 0, -1, self.text)

    def wrap(self, aW, aH) :
        canv = self.canv
        return canv._leading, canv.stringWidth(self.text)


class RotatedParagraph(Flowable):
    '''Rotates a paragraph'''
    def __init__(self, paragraph, aW, aH):
        self.paragraph = paragraph
        self.width = aW
        self.height = aH
        print 'W: ', self.width, ' H: ', self.height
    def draw(self):
        canv = self.canv
        canv.rotate(90)
        self.paragraph.wrap(self.width, self.height)
        #drawOn(canvas, x, y)
        self.paragraph.drawOn(canv, -(self.width / 2) + 15, -(self.height))

