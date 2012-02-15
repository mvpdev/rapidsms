#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from dateutil.relativedelta import *

from django.utils.translation import ugettext as _

from reportgen.timeperiods import PeriodType, Period, SubPeriod

import bonjour.dates

class FourWeeks(PeriodType):

    title       = _("Four weeks")
    description = _("Set of four seven-day weeks starting "\
                    "on a Monday X weeks ago")
    code        = '4W'
    n_periods   = 52

    @classmethod
    def periods(cls): 
        return [FourWeeks._monthly_period(index) \
            for index in xrange(0, cls.n_periods)]

    @classmethod
    def _monthly_subperiod(cls, period_start_date, index):
        # start_date is a Monday, so this subperiod ends
        # on the following Sunday
        start_date = period_start_date + relativedelta(weeks=index)
        end_date = start_date + relativedelta(weekday=SU,\
            hour=23, minute=59, second=59, microsecond=999999)

        title = _("Week of %(start)s") % \
            {'start': bonjour.dates.format_date(start_date, format="dd MMM")}
        return SubPeriod(\
            title,
            start_date,
            end_date)

    @classmethod
    def _monthly_period(cls, index):
        # Index 0 == last Monday
        # Index 1 == two Mondays ago
        start_date = datetime.today() + \
                    relativedelta(weekday=MO(-(index+1)), hour=0, minute=0,\
                        second=0, microsecond=0)
        sub_periods = [cls._monthly_subperiod(start_date, sub_index) \
            for sub_index in xrange(0,4)]

        end_date = sub_periods[len(sub_periods)-1].end
        title = _("Weeks %(start)s to %(end)s") % \
            {'start': bonjour.dates.format_date(start_date, format='medium'),
            'end': bonjour.dates.format_date(end_date, format='medium')}
        relative_title = _("Monday %(n)d week(s) ago") % \
            {'n': index}
            
        return Period(title, relative_title, \
            start_date, end_date, sub_periods)
        


