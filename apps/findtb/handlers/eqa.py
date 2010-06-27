#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.db import IntegrityError

from django_tracking.models import TrackedItem

from findtb.models import *
from findtb.libs.utils import registered, send_msg
from findtb.exceptions import ParseError, NotAllowed


READY_KEYWORD = 'ready'

KEYWORDS = [
    READY_KEYWORD,
]


@registered
def handle(keyword, params, message):

    reporter = message.persistant_connection.reporter
    # Map keyword to handler function
    {
        READY_KEYWORD: ready,
    }[keyword](params, reporter, message)


def ready(params, reporter, message):

    if reporter.groups.filter(name='dtu focal person').count():

        if len(params) > 0:
            raise ParseError(u'FAILED: the "ready" keyword should '\
                             u'be sent without anything else')

        role = reporter.role_set.get(group__name="dtu focal person")
        dtu = role.location
        district = role.location.parent

        # DTLS must exists
        try:
            dtls = Role.objects.get(group__name='district tb supervisor',
                                    location=district)
        except Role.DoesNotExist:
            raise NotAllowed(u"FAILED: No DTLS is registered for your district."
                             u"Please contact your DTLS so he registers with "\
                             u"the system.")

        try:
            sb = SlidesBatch(location=dtu, created_by=reporter)
            sb.save()
        # one slides batch by quarter and dtu
        except IntegrityError:
            raise NotAllowed(u"FAILED: you already started EQA for this "\
                             u"quarter in this DTU.")

        # set batch in state "ready"

        state = EqaStarts(slides_batch=sb)
        state.save()
        TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: Your DTLS is being notified.")

        send_msg(dtls, u"Slides from %s are ready to be picked up" % dtu.name)

    else:
         raise NotAllowed(u"You are not allowed to use this keyword. Only "\
                          u"DTU/First Controller/Second Controller Focal "\
                          u"Persons are.")