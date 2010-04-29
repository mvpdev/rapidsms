#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from findtb.models import *
from findtb.utils import registered

UNREGISTER_KEYWORD = 'unregister'

KEYWORDS = [
    UNREGISTER_KEYWORD,
]

@registered
def handle(keyword, params, message):
    if keyword==UNREGISTER_KEYWORD:
        reporter = message.persistant_connection.reporter
        if reporter:
            for role in reporter.role_set.all():
                role.delete()
            reporter.is_active=False
            reporter.save()
            message.respond("You have been unregistered. Thank you for your "
                            "time.")

