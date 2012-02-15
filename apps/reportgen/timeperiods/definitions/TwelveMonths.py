#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

class TwelveMonths(PeriodType):

    title       = _("12 Months (by Month)")
    description = _("Twelve calendar months starting X months ago")
    code        = 'TM'
    n_periods   = 24

    @classmethod
    def periods(cls): 
        return [cls._twelvemonth_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _twelvemonth_period(cls, index):
        # Index == 0 means starting this month
        # Index == 1 means starting last month

        # If we are in March, 12 month starts last April
        # e.g., We go from April 1, 2010 to March 31, 2011

        # First day of next month, starting one year ago 
        start_date = datetime.today() + \
            relativedelta(day=1, months=1-index, years=-1, hour=0, \
                minute=0, second=0, microsecond=0)

        # Last day of this month
        end_date = start_date + relativedelta(years=1, days=-1,\
            hour=23, minute=59, second=59, microsecond=999999)
      
        sub_periods = [cls._monthly_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, 12)]

        title = _("%(start)s to %(end)s (Monthly)") % \
            {'start': start_date.strftime("%b %Y"),
            'end': end_date.strftime("%b %Y")}

        relative_title = _("12 months starting %(start)d months ago") % \
                {'start': index+12}
            
        return Period(title, relative_title, \
            start_date, end_date, sub_periods)

    @classmethod
    def _monthly_subperiod(cls, period_start_date, index):
        start_date = period_start_date + relativedelta(months=index, day=1)
        end_date = start_date + relativedelta(day=31, hour=23,\
            minute=59, second=59, microsecond=999999)

        title = start_date.strftime("%b %Y")
        return SubPeriod(\
            title,
            start_date,
            end_date)


