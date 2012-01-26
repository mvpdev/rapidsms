#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

import bonjour.dates

class MonthByDays(PeriodType):

    title       = _("Month (Daily)")
    description = _("One calendar month X months ago (by day)")
    code        = 'MD'
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
     
        sub_periods = [cls._day_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, end_date.day)]

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
    def _day_subperiod(cls, period_start_date, index):
        start_date = period_start_date + relativedelta(days=index)
        end_date = start_date + \
            relativedelta(hour=23, minute=59, second=59, microsecond=999999)

        title = bonjour.dates.format_date(start_date, format="dd MMM")
        return SubPeriod(\
            title,
            start_date,
            end_date)


