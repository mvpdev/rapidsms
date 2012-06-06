#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

import bonjour.dates


class SixMonths(PeriodType):

    title       = _("6 Months (by Month)")
    description = _("Six calendar months starting X months ago")
    code        = 'SM'
    n_periods   = 24

    @classmethod
    def periods(cls):
        return [cls._sixmonth_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _sixmonth_period(cls, index):
        # Index == 0 means starting this month
        # Index == 1 means starting last month

        # If we are in March, 6 month starts last October
        # e.g., We go from October 1, 2010 to March 31, 2011

        # First day of next month, starting six months ago
        start_date = datetime.today() + \
            relativedelta(day=1, months=-index, hour=0, \
                minute=0, second=0, microsecond=0)

        # Last day of this month
        end_date = start_date + relativedelta(months=6, days=-1,\
            hour=23, minute=59, second=59, microsecond=999999)

        sub_periods = [cls._monthly_subperiod(start_date, sub_index) \
            for sub_index in xrange(0, 6)]

        title = _("%(start)s to %(end)s (Monthly)") % \
            {'start': start_date.strftime("%b %Y"),
            'end': end_date.strftime("%b %Y")}

        relative_title = _("6 months starting %(start)d months ago") % \
                {'start': index+6}

        title = _("%(start)s to %(end)s (Monthly)") % \
            {'start': start_date.strftime("%b %Y"),
            'end': end_date.strftime("%b %Y")}

        relative_title = _("6 months starting %(start)d months ago") % \
                {'start': index+6}
                
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
