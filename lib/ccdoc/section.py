
from text import Text

class PageBreak(object):
    def __init__(self):
        pass

class Section(Text):
    ''' Section is a section heading...

        You cannot modify the style of a section
        heading -- you can only pass it a string
        for a title.
    '''
    section_name = None

    def __init__(self, text, section_name=None):
        Text.__init__(self, text)
        if section_name is None:
            self.section_name = text
        else:
            self.section_name = section_name

