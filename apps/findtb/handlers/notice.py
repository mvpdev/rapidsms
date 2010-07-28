#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from findtb.models import *
from findtb.libs.utils import registered
from findtb.exceptions import *

NOTICE_KEYWORD = 'notice'

KEYWORDS = [
    NOTICE_KEYWORD,
]

@registered
def handle(keyword, params, message):
    if keyword==NOTICE_KEYWORD:
        reporter = message.persistant_connection.reporter

    roles = Role.objects.exclude(location=None).filter(reporter=reporter)
    if roles.count() == 0:
        raise NotAllowed(u"You are not allowed to send notices.")

    if len(params) == 0:
        raise BadValue(u"You must include your message after the %(key)s " \
                        "keyword." % {'key': NOTICE_KEYWORD.upper()})

    notice = Notice(reporter=reporter, location=roles[0].location, \
                    text=' '.join(params))
    notice.save()

    message.respond(u"Your notice has been received. You should receive " \
                     "a response within 48 hours.")
