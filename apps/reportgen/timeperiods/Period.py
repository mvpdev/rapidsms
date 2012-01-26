#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

class Period(object):
    def __init__(self, title, relative_title, \
        start, end, sub_periods):
        self.title = title
        self.relative_title = relative_title
        self.start = start
        self.end = end
        self._sub_periods = sub_periods

    def __repr__(self):
        return "<Period: %s>" % self.title

    # This is a method to be consistent
    # with PeriodType.
    # You do FourWeeks.periods()
    # so you do ThisMonth.sub_periods()

    def sub_periods(self):
        return self._sub_periods
