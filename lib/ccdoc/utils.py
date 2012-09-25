import random
import string
import os

from django.conf import settings

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

def font_path(font_name):
    filedir = os.path.dirname(__file__)
    return os.path.join(filedir, 'fonts', font_name)

def register_fonts():
    """
    register_fonts() loads the non-standard fonts
    used for Ethiopic script.

    Note: The only font we have that supports both
    Ethiopic script and Latin script is FreeSerif.
    
    When you are designing a report that should work
    across sites, make sure that you *only* use the
    FreeSerif font. If you need to make something
    bold or italic, use the <b> and <i> tags.
    That way your report will work with all scripts.
    """

    pdfmetrics.registerFont(TTFont('LiberationSans', \
                                   font_path('LiberationSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('LiberationSans-Bold', \
                                   font_path('LiberationSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('LiberationSans-Italic', \
                                   font_path('LiberationSans-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('LiberationSans-BoldItalic', \
                                   font_path('LiberationSans-BoldItalic.ttf')))
    registerFontFamily('LiberationSans', normal='LiberationSans', \
                       bold='LiberationSans-Bold', \
                       italic='LiberationSans-Italic', \
                       boldItalic='LiberationSans-BoldItalic')

    # FreeSans
    pdfmetrics.registerFont(TTFont('FreeSans', \
                                   font_path('FreeSans.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSansBold', \
                                   font_path('FreeSansBold.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSansItalic', \
                                   font_path('FreeSansOblique.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSansBoldItalic', \
                                   font_path('FreeSansBoldOblique.ttf')))

    registerFontFamily('FreeSans', normal='FreeSans', \
                       bold='FreeSansBold', \
                       italic='FreeSansItalic', \
                       boldItalic='FreeSansBoldItalic')

    # FreeSerif
    pdfmetrics.registerFont(TTFont('FreeSerif', \
                                   font_path('FreeSerif.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSerifBold', \
                                   font_path('FreeSerifBold.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSerifItalic', \
                                   font_path('FreeSerifItalic.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSerifBoldItalic', \
                                   font_path('FreeSerifBoldItalic.ttf')))

    
    # Check if we're using an Ethiopic language (like Amharic)
    # If so, we can't use bold or italics, so map those away
    is_eth = (settings.LANGUAGE_CODE.startswith('am'))
    
    registerFontFamily('FreeSerif', normal='FreeSerif', \
                       bold='FreeSerif' + ('' if is_eth else 'Bold'), \
                       italic='FreeSerif' + ('' if is_eth else 'Italic'), \
                       boldItalic='FreeSerif' + ('' if is_eth else 'BoldItalic'))


def str_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """Generates random strings"""
    return ''.join(random.choice(chars) for x in range(size))