import string
try:
    from xlwt import Workbook, XFStyle, Font
except ImportError:
    pass

from generator import Generator

VALID_CHARS = string.digits + string.letters + ' _()|'

def clean_string(s):
    return str(filter(lambda x: x in VALID_CHARS, s)[0:31])

class ExcelGenerator(Generator):
    def _start_document(self):
        ''' Flag that's true when the first sheet
            contains a section header.  This is so
            the first section is on the first sheet
            and every next section is on a new sheet.
        '''
        self.has_section = False

        self.workbook = Workbook(encoding='utf-8')

        ''' All worksheets '''
        self.sheets = [self.workbook.add_sheet(clean_string(self.title))]

        ''' Pointer to current worksheet '''
        self.cur_sheet = self.sheets[0]

        ''' Pointer into our location in spreadsheet grid '''
        self.row = 0
        self.col = 0

        title_style = XFStyle()
        title_style.font.bold = True
        title_style.font.height = 500
        
        sub_style = XFStyle()
        sub_style.font.italic = True

        self.cur_sheet.write_merge( \
            self.row, self.row+1, \
            self.col, self.col+6, \
            self.title, title_style)
        self.row += 2
        self.cur_sheet.write(self.row, self.col, \
            self.datestring)
        self.row += 1

        if self.subtitle != None and self.subtitle != '':
            self.cur_sheet.write(self.row, self.col, \
                self.subtitle, sub_style)
            self.row += 2
        else:
            self.row += 1

    def _render_section(self, section):
        self.row += 1
        if self.has_section:
            s = self.workbook.add_sheet(section.section_name)
            self.row = 0
            self.col = 0
            self.sheets.append(s)
            self.cur_sheet = s
        else:
            self.has_section = True
            self.cur_sheet.name = section.text
        
        style = XFStyle()
        style.font.bold = True
        style.font.height = 300

        self.cur_sheet.write_merge( \
            self.row, self.row+1, \
            self.col, self.col+6, \
        section.text, style)
        self.row += 2

    def _render_pagebreak(self, pagebreak):
        pass

    def _render_paragraph(self, paragraph):
        s = u''
        for t in paragraph.contents:
            s += t.text
        self.cur_sheet.write(self.row, self.col, s)
        self.row += 1

    def _render_hline(self, hline):
        self.row += 1
        
    def _render_table(self, table):
        style = XFStyle()
        
        if table.title != None: 
            bold_style = XFStyle()
            bold_style.bold = True
            self.cur_sheet.write(self.row, self.col, \
                unicode(table.title.text), bold_style)
            self.row += 1
       
        oldcol = self.col
        ''' Iterate through each table row '''
        for row in table.rows:
            self.col = oldcol
            ''' Iterate through each table column '''
            for col in row[1]:
                style.font.bold = False
                style.font.italic = False
                
                if row[0]: style.font.bold = True
                if col.bold: style.font.bold = True
                if col.italic: style.font.italic = True

                self.cur_sheet.write(
                    self.row, self.col,
                    col.text,
                    style)
               
                self.col += 1
            self.row += 1
        self.col = oldcol

    def _end_document(self):
       self.workbook.save(self._filename) 
        
