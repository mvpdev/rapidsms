#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

import bonjour.dates

class Month(PeriodType):

    title       = _("Month")
    description = _("One calendar month X months ago")
    code        = 'M'
    n_periods   = 24

    @classmethod
    def periods(cls): 
        return [cls._monthly_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _monthly_period(cls, index):
        # Index == 0 means next month
        # Index == 1 means this month

        # First day of month, starting next month
        start_date = datetime.today() + \
            relativedelta(day=1, months=-index, hour=0, \
                minute=0, second=0, microsecond=0)


        # Last day of calendar month
        end_date = start_date + \
            relativedelta(day=31, hour=23, minute=59, second=59,\
                microsecond=999999)
      
        # If we need five weeks to encompass the entire
        # month, then make it so
        if end_date.day > 28:
            weeks = 5
        else:
            weeks = 4

        sub_periods = [cls._monthly_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, weeks)]

        title = _("%(start)s") % \
            {'start': start_date.strftime("%B %Y")}
        if index == 0:
            relative_title = _("This month")
        elif index == 1:
            relative_title = _("Last month")
        else:
            relative_title = _("%(start)s months ago") % \
                {'start': index}
            
        return Period(title, relative_title, \
            start_date, end_date, sub_periods)

    @classmethod
    def _monthly_subperiod(cls, period_start_date, index):
        start_date = period_start_date + relativedelta(weeks=index)
        end_date = start_date + \
            relativedelta(day=(start_date.day+6), hour=23, minute=59,\
                second=59, microsecond=999999)

        title = _("%(start)s to %(end)s") % \
            {'start': bonjour.dates.format_date(start_date, format="dd MMM"), 
            'end': bonjour.dates.format_date(end_date, format="dd MMM")}
        return SubPeriod(\
            title,
            start_date,
            end_date)


