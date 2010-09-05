#!/usr/bin/env python
# -*- coding= UTF-8 -*-

import datetime

def humanize_timedelta(previous_date,
                       max_days=3,
                       datetime_format='%m/%d/%Y',
                       suffix=' ago'):
    """
    Returns a humanized string representing a fuzzy time difference
    between the current date and the passed date.

    >>> yesterday = datetime.datetime.now() - datetime.timedelta(1)
    >>> humanize_timedelta(yesterday)
    u'yesterday'
    >>> humanize_timedelta(yesterday - datetime.timedelta(1))
    u'2 days ago'
    >>> humanize_timedelta(yesterday - datetime.timedelta(2))
    u'3 days ago'
    >>> four_days = yesterday - datetime.timedelta(3)
    >>> humanize_timedelta(four_days) == four_days.strftime("%m/%d/%Y")
    True
    >>> humanize_timedelta(four_days,
    ... datetime_format="%d/%m/%y") == four_days.strftime("%d/%m/%y")
    True
    >>> humanize_timedelta(four_days) == four_days.strftime("%m/%d/%Y")
    True
    >>> humanize_timedelta(four_days, max_days=4)
    u'4 days ago'
    >>> three_hours = datetime.datetime.now() - datetime.timedelta(hours=3)
    >>> humanize_timedelta(three_hours)
    u'3 hours ago'
    >>> three_mins = datetime.datetime.now() - datetime.timedelta(minutes=3)
    >>> humanize_timedelta(three_mins)
    u'3 minutes ago'
    >>> three_secs = datetime.datetime.now() - datetime.timedelta(seconds=3)
    >>> humanize_timedelta(three_secs)
    u'3 seconds ago'
    >>> humanize_timedelta(three_secs, suffix=" before the end of the word")
    u'3 seconds before the end of the word'
    """

    today = datetime.datetime.now()
    delta = today - previous_date
    time_values = (
        (u"day", delta.days),
        (u"hour", delta.seconds / 3600),
        (u"minute", delta.seconds % 3600 / 60),
        (u"second", delta.seconds % 3600 % 60),
    )

    if time_values[0][1] > max_days:
        return previous_date.strftime(datetime_format)

    if (today.date() - previous_date.date()).days == 1:
        return u"yesterday"

    for tStr, value in time_values:
        if value > 0:
            return u"%s %s%s" % (value,
                                 tStr if value == 1 else tStr + u"s",
                                 suffix)

    return u"0 second " + suffix

