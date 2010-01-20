#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

''' Helper functions for use in App and U.I '''

from datetime import datetime


def month_end(date):
    ''' date of last day in month.

    return date '''
    for n in (31, 30, 28):
        try:
            return date.replace(day=n)
        except:
            pass
    return date


def next_month(date):
    ''' date of same day next month.

    return date '''
    if date.day > 28:
        day = 28
    else:
        day = date.day
    if date.month == 12:
        month = 1
        year = date.year + 1
    else:
        month = date.month + 1
        year = date.year

    return date.replace(day=day, month=month, year=year)


def day_start(date):
    ''' begining of day from date.

    return datetime '''
    t = date.time().replace(hour=0, minute=1)
    return datetime.combine(date.date(), t)


def day_end(date):
    ''' end of day from date.

    return datetime '''
    t = date.time().replace(hour=23, minute=59)
    return datetime.combine(date.date(), t)
