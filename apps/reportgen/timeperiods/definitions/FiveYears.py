#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

class FiveYears(PeriodType):

    title       = _("5 Years")
    escription = _("Five calendar years")
    code        = '5Y'
    n_periods   = 10

    @classmethod
    def periods(cls): 
        return [cls._five_year_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _five_year_period(cls, index):
        # Index == 0 means starting this year
        # Index == 1 means starting last year

        start_date = datetime.today() + \
            relativedelta(day=1, month=1, years=-index,\
                hour=0, minute=0, second=0, microsecond=0)

        # Last day of this month
        end_date = start_date + \
            relativedelta(month=12, day=31, years=4,\
            hour=23, minute=59, second=59, microsecond=999999)
      
        sub_periods = [cls._annual_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, 5)]

        title = _("Years %(start)s - %(end)s") % \
            {'start': start_date.strftime("%Y"),\
            'end': end_date.strftime("%Y")}

        relative_title = _("Five years starting %(start)d years ago") % \
                {'start': index}
            
        return Period(title, relative_title, \
            start_date, end_date, sub_periods)

    @classmethod
    def _annual_subperiod(cls, period_start_date, index):
        start_date = period_start_date + relativedelta(years=index, day=1)
        end_date = start_date + \
            relativedelta(month=12, day=31, \
                hour=23, minute=59, second=59, microsecond=999999)

        title = start_date.strftime("%Y")
        return SubPeriod(\
            title,
            start_date,
            end_date)


