#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from django.db import IntegrityError

from django_tracking.models import TrackedItem

from locations.models import Location

from findtb.models import *
from findtb.libs.utils import registered, send_msg, send_to_dtls send_to_dtu_focal_person
from findtb.exceptions import ParseError, NotAllowed, BadValue


START_KEYWORD = 'start'
COLLECT_KEYWORD = 'collect'
READY_KEYWORD = 'ready'
RECEIVE_KEYWORD = 'receive'

KEYWORDS = [
    START_KEYWORD,
    COLLECT_KEYWORD,
    RECEIVE_KEYWORD,
    READY_KEYWORD
]


@registered
def handle(keyword, params, message):

    reporter = message.persistant_connection.reporter
    # Map keyword to handler function
    {
        START_KEYWORD: start,
        COLLECT_KEYWORD: collect,
        READY_KEYWORD: ready,
        RECEIVE_KEYWORD: receive,
    }[keyword](params, reporter, message)



def start(params, reporter, message):
    """

    /!\ This function is not going to be used in production. We let it
    here because it's handy for testing and harmless. This do what the
    previous 'ready' did, but it should no in the training documentation.

    Call back function called when a DTU notifies the system that slides
    are ready for collection.
    """
    if reporter.groups.filter(name='dtu focal person').count():

        if len(params) > 0:
            raise ParseError(u'FAILED: the "start" keyword should '\
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
         raise NotAllowed(u"You are not allowed to use the 'START' keyword. Only "\
                          u"DTU Focal Persons are.")


def collect(params, reporter, message):
    """
    Triggered when DTLS or ZTLS comes to pick up slides.
    """

    if reporter.groups.filter(name='district tb supervisor').count():
        format_error = u"Collection failed: you must send: "\
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

        number = int(groupdict['number'])
        if 20 < number < 5:
            raise BadValue(u"Collection failed: you must collect between 5 "\
                           u"and 20 slides. You entered %s." % number)

        # slides batch must exists to be collected
        try:
            sb = SlidesBatch.objects.get_for_quarter(location)
        except SlidesBatch.DoesNotExist:
            raise BadValue(u"Collection failed: %s never notified the "\
                           u"system it started EQA. Ask the DTU Focal Person "\
                           u"to send the 'START' keyword." % location.name)

        # slides batch must be in ready state
        ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
        if ti.state.title != 'eqa_starts':
            raise BadValue(u"Collection failed: slides from %s have already "\
                           u"been collected" % location.name)

        # set batch in state "collected_from_dtu"

        state = CollectedFromDtu(slides_batch=sb)
        state.save()
        TrackedItem.add_state_to_item(sb, state)

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


def receive(params, reporter, message):
    """
    Triggered when Control Focal Persons notify they received slides
    """

    if reporter.groups.filter(name='first control focal person').count():

        format_error = u"Reception failed: you must send: "\
                       u"'RECEIVE LocationCode' or 'RECEIVE all'. You can "\
                       u"send several codes at the same time: "\
                       u"'RECEIVE LocationCode1 LocationCode2'. Location "\
                       u"must all be DTUs."

        # syntax check for the sms
        text = ' '.join(params)
        regex = r'''
                 (?:
                  ^(\d+[\-,./]+\d+)                # first dtu code
                  (?:$|(?:\s+(\d+[\-,./]+\d+))*)$  # following dtu codes if any
                 ) | all                           # or 'all' keyword
                 '''

        # check syntax
        if not re.match(regex, text, re.VERBOSE):
            raise ParseError(format_error)

        # extract codes
        codes = re.findall(r'\D*(\d+[\-,./]+\d+|all)\D*', text)

        # if 'all', receive every collected slides
        if codes[0] == 'all':
            district = reporter.role_set.get(group__name='first control focal person').location
            dtus = district.descendants()
            accepted_batches = []
            for dtu in dtus:
                try:
                    sb = SlidesBatch.objects.get_for_quarter(dtu)
                except SlidesBatch.DoesNotExist:
                    pass
                else:
                    ti, c = TrackedItem.get_tracker_or_create(sb)
                    if ti.state.title == 'collected_from_dtu':
                        accepted_batches.append(sb)

            if not accepted_batches:
                raise BadValue(u"No slides are on their way to first control "\
                               u"in your district")

        # check is codes are valid and for a DTU
        else:
            dtus = []
            not_dtus = []
            for code in codes:
                try:
                    dtus.append(Location.objects.get(type__name=u'dtu',
                                                     code=code))
                except Location.DoesNotExist:
                    not_dtus.append(code)
            if not_dtus:
                if len(not_dtus) > 1:
                    msg = u"Reception failed: %(codes)s are not " \
                               u"valid DTU codes. Please correct and " \
                               u"send again."
                else:
                    msg = u"Reception failed: %(codes)s is not a " \
                           u"valid DTU code. Please correct and " \
                           u"send again."
                raise BadValue(msg % {'codes': ', '.join(not_dtus)})

            # check that these slides are meant to go to first control
            accepted_batches = []
            rejected_batches = []

            for dtu in dtus:
                sb = SlidesBatch.objects.get_for_quarter(dtu)
                ti, c = TrackedItem.get_tracker_or_create(sb)
                if ti.state.title != 'collected_from_dtu':
                    rejected_batches.append(sb.location.name)
                else:
                    accepted_batches.append(sb)

            if rejected_batches:
                raise BadValue(u"Reception failed: slides from %(codes)s are not " \
                               u"in their way to First Control. Check they have" \
                               u"been collected by DTLS and didn't pass first "\
                               u"control already." % {
                               'codes': ', '.join(rejected_batches)})

        codes = ', '.join(sb.location.code for sb in accepted_batches)
        for sb in accepted_batches:
            state = DeliveredToFirstController(slides_batch=sb)
            state.save()
            TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: slides from %(codes)s are ready for first "\
                        u"control" % {
                        'codes': codes
                        })

        send_to_dtls(sb.location,
                     u"Slides from %(codes)s have been received by first "\
                     u"controller" % {
                        'codes': codes
                        })

        for dtu in dtus:
            send_to_dtu_focal_person(dtu,
                                     u"EQA slides arrived at first control")

    else:
         raise NotAllowed(u"You are not allowed to use this keyword. Only "\
                          u"First and Second Control Focal Persons are.")


def ready(params, reporter, message):
    """
    Triggered when Control Focal persons notify slid are ready to be picked up.
    """
    # TODO : ready()
    pass
