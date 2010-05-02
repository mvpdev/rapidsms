#!/usr/bin/env python
# -*- coding= UTF-8 -*-


from django import template
register = template.Library()
from findtb.libs.format_timedelta import humanize_timedelta

@register.filter("humanize_time_delta")
def humanize_time_delta(value):
    return humanize_timedelta(value)