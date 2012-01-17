#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' Bonjour date helpers '''
import pytz
import datetime 

from babel import Locale
import babel.dates

from bonjour.ethiopian_date import EthiopianDateConverter

from django.conf import settings

TIGRINYA_MONTHS_ABBREVIATED = {
   1 : u"\u1218\u1235\u12a8",
   2 : u"\u1325\u1245\u121d",
   3 : u"\u1215\u12f3\u122d",
   4 : u"\u1273\u1215\u1233",
   5 : u"\u1325\u122a",
   6 : u"\u1208\u12ab\u1272",
   7 : u"\u1218\u130b\u1262",
   8 : u"\u121a\u12eb\u12dd",
   9 : u"\u130d\u1295\u1266",
   10 : u"\u1230\u1290",
   11 : u"\u1213\u121d\u1208",
   12 : u"\u1290\u1213\u1230",
   13 : u"\u1333\u1309",
}
"""Abbreviated month names in Tigrinyna"""

TIGRINYA_MONTHS_WIDE = {
   1 : u"\u1218\u1235\u12a8\u1228\u121d",
   2 : u"\u1325\u1245\u121d\u1272",
   3 : u"\u1215\u12f3\u122d",
   4 : u"\u1273\u1215\u1233\u1235",
   5 : u"\u1325\u122a",
   6 : u"\u1208\u12ab\u1272\u1275",
   7 : u"\u1218\u130b\u1262\u1275",
   8 : u"\u121a\u12eb\u12dd\u12eb",
   9 : u"\u130d\u1295\u1266\u1275",
   10 : u"\u1230\u1290",
   11 : u"\u1213\u121d\u1208",
   12 : u"\u1290\u1213\u1230",
   13 : u"\u1333\u1309\u121c",
}
"""Full month names in Tigrinyna"""

def _django_locale():
    return Locale.parse(settings.LANGUAGE_CODE.replace('-','_'))

def _format_date_ethiopian(date, format):
    """Converts the input date to the Julian/Ethiopian
    calendar and formats a date in the ti_ET locale for
    Tigrinya.
    """

    locale = Locale.parse('ti_ET')
    
    if date is None:
        date = datetime.date.today()

    # Day of week with Monday=0
    dow = date.isoweekday() - 1

    # Convert date to Julian calendar
    (jyear, jmonth, jday) = EthiopianDateConverter.date_to_ethiopian(date)
   
    # Uses the babel.dates codes for substitutions
    sub_dict = {
        'EEEE': locale.days['format']['wide'][dow],
        'EEE': locale.days['format']['abbreviated'][dow],
        'MMMM': TIGRINYA_MONTHS_WIDE[jmonth],
        'MMM': TIGRINYA_MONTHS_ABBREVIATED[jmonth],
        'MM': "%02d" % jmonth,
        'M': "%d" % jmonth,
        'dd': "%02d" % jday,
        'd': "%d" % jday,
        'yyyy': "%04d" % jyear,
        'yy': "%02d" % (jyear % 100),
        'G': locale.eras['abbreviated'][1],
    }

    try:
        if format in locale.date_formats:
            return locale.date_formats[format].format % sub_dict
        else:
            return babel.dates.parse_pattern(format).format % sub_dict
    except KeyError, err:
        raise ValueError("Date format %s not defined" % err)

def format_date(date=None, format='medium', locale=None):
    """
    Format date using the server's locale
    as specified in :file:`settings.py`.
    Uses the Julian calendar for Ethiopian dates
    (language codes "ti" and "am") and the Gregorian
    calendar for other dates.

    :param date: Date to format
    :type date: :class:`datetime.date`
    :param format: "short", "medium", "long", "full"
    :type format: :class:`str`
    :param locale: The locale to use (defaults to server locale
                   as specified in `settings.LANGUAGE_CODE`
    :type locale: :class:`str`
    """

    l = None
    if locale is None:
        l = _django_locale() 
    else:
        l = Locale.parse(locale)

    if l.language in ('am','ti'):
        # For our purposes, we assume that Amaharic means 
        # Tigrinya. This is because CC+ is only used in 
        # Tigrinya-speaking regions for now and Django does
        # not support the "ti" language code, so we use "am"
        # to mean "Tigrinya".
        return _format_date_ethiopian(date, format)

    else: 
        return babel.dates.format_date(date, format, _django_locale())

def format_time(time=None, format='medium', tzinfo=None, locale=None):
    """Alias to :func:`babel.dates.format_time` which
    defaults to the Django locale and time zone
    """
    if locale is None:
        locale = _django_locale()
    if tzinfo is None:
        tzinfo = pytz.timezone(settings.TIME_ZONE)

    try:
        return babel.dates.format_time(time, format, tzinfo, locale)
    except KeyError:
        # in case format full fails use long, fixes #820 for Rwanda
        format = u'long'
        return babel.dates.format_time(time, format, tzinfo, locale)

def format_datetime(datetime=None, format='medium', locale=None):
    """Alias to :func:`babel.dates.format_datetime` which
    defaults to the Django locale and time zone
    """
    if locale is None:
        locale = _django_locale()

    # Borrowed from babel
    return babel.dates.get_datetime_format(format, locale=locale)\
        .replace('{0}', format_time(datetime, format, locale=locale))\
        .replace('{1}', format_date(datetime, format, locale=locale))
    
