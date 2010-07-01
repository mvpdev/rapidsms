#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from django.db import IntegrityError

from django_tracking.models import TrackedItem

from locations.models import Location

from findtb.models import *
from findtb.libs.utils import registered, send_msg
from findtb.exceptions import ParseError, NotAllowed, BadValue


READY_KEYWORD = 'ready'
COLLECT_KEYWORD = 'collect'

KEYWORDS = [
    READY_KEYWORD,
    COLLECT_KEYWORD
]


@registered
def handle(keyword, params, message):

    reporter = message.persistant_connection.reporter
    # Map keyword to handler function
    {
        READY_KEYWORD: ready,
        COLLECT_KEYWORD: collect,
    }[keyword](params, reporter, message)


def ready(params, reporter, message):
    """
    Call back function called when a DTU/First Controller/Second Controller
    Focal Person notifies the system that slides are ready for collection.
    """
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

        state = EqaStarts(slides_batch=sb)
        state.save()
        TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: Your DTLS is being notified that slides are ready.")

        send_msg(dtls, u"Slides from %s are ready to be picked up for EQA" % dtu.name)

    else:
         raise NotAllowed(u"You are not allowed to use the 'COLLECT' keyword. Only "\
                          u"DTU/First Controller/Second Controller Focal "\
                          u"Persons are.")


def collect(params, reporter, message):

    if reporter.groups.filter(name='district tb supervisor').count():
        format_error = u"Collection failed:, you must send: "\
                       u"COLLECT LocationCode NumberOfSlides"

        # syntax check for the sms
        l = len(params)
        if l < 2:
            raise ParseError(format_error)

        text = ' '.join(params)
        if l == 2:
            regex = r'(?P<prefix>[0-9\-,./]+)\s+(?P<number>\d+)'
        else:
            regex = r'(?P<prefix>\d+)[ \-,./]+(?P<suffix>\d+)\s+(?P<number>\d+)'

        match = re.match(regex, text)
        if not match:
            raise ParseError(format_error)

        groupdict = match.groupdict()

        # check if the location code exists
        if groupdict.get('suffix', None) is not None:
            try:
                code = '-'.join((groupdict['prefix'], groupdict.get('suffix', '')))
                location = Location.objects.get(code__iexact=code)
            except Location.DoesNotExist:
                raise BadValue(u"Collection failed: %(code)s is not a " \
                               u"valid location code. Please correct and " \
                               u"send again." % \
                               {'code': code})
        else:
            code = groupdict['prefix']
            try:
                location = Location.objects.get(code__iexact=code)
            except Location.DoesNotExist:
                raise BadValue(u"Collection failed: %(code)s is not a " \
                               u"valid location code. Please correct and " \
                               u"send again." % \
                               {'code':code})

        # location must be a dtu
        if location.type.name != 'dtu':
            raise BadValue(u"Collection failed: %s is not a DTU" % location.name)

        # slides batch must exists to be collected
        try:
            sb = SlidesBatch.objects.get_for_quarter(location)
        except SlidesBatch.DoesNotExist:
            raise BadValue(u"Collection failed: %s never notified the "\
                           u"system it started EQA. Ask the DTU Focal Person "\
                           u"to send the 'READY' keyword." % location.name)

        # slides batch must be in ready state
        ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
        if ti.state.title != 'eqa_starts':
            raise BadValue(u"Collection failed: slides from %s have already "\
                           u"been collected" % location.name)

        # set batch in state "collected_from_dtu"

        state = CollectedFromDtu(slides_batch=sb)
        state.save()
        TrackedItem.add_state_to_item(sb, state)

        number = int(groupdict['number'])

        # create slides and attache to batch
        for i in range(number):
            Slide(batch=sb).save()

        message.respond(u"SUCCESS: %(number)s slides from %(dtu)s "\
                        u"are registered for EQA." % {'dtu': location.name,
                                                      'number': number })

        dtu_focal_person = Role.objects.get(location=location).reporter

        send_msg(dtu_focal_person,
                 u"DTLS have reported picking up %(number)s slides from your "\
                 u"DTU for EQA." % {'number': number })

    else:
         raise NotAllowed(u"You are not allowed to use this keyword. Only "\
                          u"DTLS and ZTLS are.")
