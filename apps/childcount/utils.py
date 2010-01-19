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

def fixMessagelogDuplicates():
    from django.db import connection
    from childcount.models.logs import MessageLog
    cursor = connection.cursor()
    """ Pick  duplicate records
    """
    cursor.execute("select id, created_at, mobile, text from  childcount_messagelog as x where (select count(*) from childcount_messagelog as q where q.created_at = x.created_at) > 1")
    cdata = cursor.fetchall()
    """ Pick distinct duplicate records
    """
    cursor.execute("select id, created_at, mobile, text from  childcount_messagelog as x where (select count(*) from childcount_messagelog as q where q.created_at = x.created_at) > 1 group by created_at")
    data = cursor.fetchall()
    c = 0
    for d in data:
        """Pick all logs with the exception of this one
        """
        ml = MessageLog.objects.filter(mobile=d[2], text=d[3], created_at=d[1]).exclude(id=d[0])
        for l in ml:
            l.delete()
            c += 1
    cursor.execute("select id, created_at, mobile, text from  childcount_messagelog as x where (select count(*) from childcount_messagelog as q where q.created_at = x.created_at) > 1")
    data = cursor.fetchall()
    print c, " out of ", len(cdata)
