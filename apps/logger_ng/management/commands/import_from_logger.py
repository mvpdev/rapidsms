#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
A helper command to export your old logger records to the new logger_ng.

To run, simply replace logger in your local.ini apps list with logger_ng, then
run: ./rapidsms import_from_logger

It will even (somewhat) intelligently associate outgoing messages with their
corresponding incoming message, based on the message identity, backend, and
timestamp.

Before importing, it will first check a random sampling of old messages
and if it finds they've already been imported, it will exit-
In other words, it won't let you accidentally import your old logs twice.
'''

import random
from datetime import timedelta

from django.utils.translation import ugettext as _
from django.core.management.base import BaseCommand, CommandError

from logger.models import IncomingMessage, OutgoingMessage
from logger_ng.models import LoggedMessage
from reporters.models import PersistantConnection


def create_from_logger_msg(msg):
    '''
    Helper function that takes either an IncomingMessage or Outgoing
    message (from the old logger app) and creates a LoggedMessage
    object from it. It saves the new LoggedMessage then returns it.
    '''
    if isinstance(msg, IncomingMessage):
        direction = LoggedMessage.DIRECTION_INCOMING
    else:
        direction = LoggedMessage.DIRECTION_OUTGOING

    try:
        reporter = PersistantConnection \
                            .objects.get(backend__slug=msg.backend,
                                         identity=msg.identity).reporter
    except PersistantConnection.DoesNotExist:
        reporter = None
    msg_lng = LoggedMessage(identity=msg.identity, backend=msg.backend,
                            text=msg.text, reporter=reporter,
                            direction=direction)
    msg_lng.save()
    msg_lng.date = msg.date
    msg_lng.save()
    return msg_lng


class Command(BaseCommand):
    '''
    This class _must_ be named command subclass BaseCommand to work.
    '''

    def handle(self, *args, **options):
        '''
        Do the import, will be called when the management call of
            ./rapidsms import_from_logger
        is called.
        '''

        # This is used to pair the outgoing message with incoming messages
        # If we find an outgoing message that was sent within
        # SECONDS_BEFORE_MATCH before the outgoing message, to the same
        # identity on the same backend, we assume that the outgoing message
        # is a response to the incoming message and we set the response_to
        # of the outgoing message to the incoming message.
        # If you don't want this behaviour, set this to 0.
        SECONDS_BEFORE_MATCH = 5

        OUTGOING = LoggedMessage.DIRECTION_OUTGOING
        INCOMING = LoggedMessage.DIRECTION_INCOMING

        if not IncomingMessage.objects.count() and \
           not OutgoingMessage.objects.count():
            raise CommandError(_(u"There are no messages in the logger app " \
                                 u"to import."))

        # First let's do a sanity check to see if we've already imported
        # We choose 5 random incoming and outgoing messages. If any of them
        # already exist in logger_ng, we exit without importing.
        checks = []
        for i in range(0, 5):
            if IncomingMessage.objects.count():
                checks.append(random.choice(IncomingMessage.objects.all()))
            if OutgoingMessage.objects.count():
                checks.append(random.choice(OutgoingMessage.objects.all()))

        for msg in checks:
            messages = LoggedMessage.objects.filter(identity=msg.identity,
                                                    backend=msg.backend,
                                                    text=msg.text,
                                                    date=msg.date)
            if (isinstance(msg, IncomingMessage) and \
               messages.filter(direction=INCOMING).count()) or \
               (isinstance(msg, OutgoingMessage) and \
               messages.filter(direction=OUTGOING).count()):
                raise CommandError(_(u"It appears that you have already " \
                                     u"imported your messages."))

        print _(u"Importing %d incoming messages...") % \
              IncomingMessage.objects.count()
        for msg in IncomingMessage.objects.all():
            msg_lng = create_from_logger_msg(msg)
            msg_lng.save()

        print _(u"Importing %d outgoing messages...") % \
              OutgoingMessage.objects.count()
        count = 0
        for msg in OutgoingMessage.objects.all():
            msg_lng = create_from_logger_msg(msg)
            if SECONDS_BEFORE_MATCH > 0:
                just_before = msg.date - \
                              timedelta(seconds=SECONDS_BEFORE_MATCH)
                try:
                    orig = LoggedMessage.incoming.get(identity=msg.identity,
                                                      backend=msg.backend,
                                                      date__gte=just_before,
                                                      date__lte=msg.date)
                except (LoggedMessage.DoesNotExist,
                        LoggedMessage.MultipleObjectsReturned):
                    pass
                else:
                    count += 1
                    msg_lng.response_to = orig
            msg_lng.save()

        print _(u"%d outgoing messages paired with " \
                u"their incoming messages.") % count

        print _(u"Importing complete.")
