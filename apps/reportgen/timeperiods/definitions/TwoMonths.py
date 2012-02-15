#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

class TwoMonths(PeriodType):

    title       = _("2 Months")
    description = _("Two consecutive calendar months")
    code        = '2M'
    n_periods   = 24

    @classmethod
    def periods(cls): 
        return [cls._twelvemonth_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _twelvemonth_period(cls, index):
        # Index == 0 means starting this month
        # Index == 1 means starting last month

        # First day of month X months ago
        start_date = datetime.today() + \
            relativedelta(day=1, months=-index, hour=0, minute=0, \
                second=0, microsecond=0)

        # Last day of month after start month
        end_date = start_date + relativedelta(months=2, days=-1, \
            hour=23, minute=59, second=59, microsecond=999999)
      
        sub_periods = [cls._monthly_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, 2)]

        title = _("%(start)s and %(end)s") % \
            {'start': start_date.strftime("%b %Y"),
            'end': end_date.strftime("%b %Y")}

        relative_title = _("2 months starting %(start)d months ago") % \
                {'start': index}
            
        return Period(title, relative_title, \
            start_date, end_date, sub_periods)

    @classmethod
    def _monthly_subperiod(cls, period_start_date, sub_index):
        start_date = period_start_date + relativedelta(months=sub_index,day=1)
        end_date = start_date + relativedelta(day=31, hour=23,\
            minute=59, second=59, microsecond=999999)

        title = start_date.strftime("%b %Y")
        return SubPeriod(\
            title,
            start_date,
            end_date)


