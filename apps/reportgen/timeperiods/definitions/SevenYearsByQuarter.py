#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

class SevenYearsByQuarter(PeriodType):

    title       = _("7 Years (by Quarter)")
    description = _("Seven Years starting X years ago")
    code        = '7Q'
    n_periods   = 12

    @classmethod
    def periods(cls): 
        return [cls._sevenyear_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _sevenyear_period(cls, index):
        # Index == 0 means starting this quarter
        # Index == 1 means starting last quarter

        # First day of quarter
        start_date = datetime.today() + \
            relativedelta(day=1, month=1,
                hour=0, minute=0, second=0, microsecond=0) + \
            relativedelta(years=-index)

        # Last day of quarter
        end_date = start_date + relativedelta(years=6,
            hour=23, minute=59, second=59, microsecond=999999)
      
        sub_periods = [cls._quarterly_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, 4*7)]

        end_qtr = end_date.month/3
        title = _("%(start)s to %(end)s") % \
            {'start': start_date.strftime("%Y"),
            'end': end_date.strftime("%Y")}

        relative_title = _("7 years starting %(start)d years ago") % \
                {'start': index}
            
        return Period(title, relative_title, \
            start_date, end_date, sub_periods)

    @classmethod
    def _quarterly_subperiod(cls, period_start_date, index):
        start_date = period_start_date + relativedelta(months=3*index, day=1)
        end_date = start_date + relativedelta(months=2,day=31,\
            hour=23, minute=59, second=59, microsecond=999999)

        qtr = (start_date.month / 3) + 1
        title = (start_date.strftime("%Y") + " Q%d" % qtr)
        return SubPeriod(\
            title,
            start_date,
            end_date)

