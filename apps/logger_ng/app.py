#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
logger_ng is an enhanced replacement for the original rapidsms logger

It should be included as the first app in your local.ini file. It performs
a number of functions:
    - Store a LoggedMessage object for every incoming and outgoing message.
    - Inject a logger_id watermark into the rapidsms Message object as
      it passes through.
    - Associate outgoing messages to their soliciting incoming message when
      Message.respond is used by an app.
    - Look-up a message's reporter and store it with the LoggedMessage
    - Store the message.status (CharField) along with the message.
    - Provide a convenient web interface to view the message log
    - Allow users to respond to messages from the web interface
    - Imports from the original logger app

logger_ng does not play well with logger. To switch from using the original
logger app, to logger_ng, simply edit your local.ini and change logger
in your apps list to logger_ng.
Then create the logger_ng table by running ./rapidsms syncdb
Import your old logs from logger by running ./rapidsms import_from_logger

Permissions:
    'logger_ng.can_view' - Required to view the logger_ng web interface
    'logger_ng.can_respond' - Required to send SMS response from the web

Conflicts:
    logger app

Dependencies:
    direct_sms and others
'''

import rapidsms

from models import LoggedMessage


class App(rapidsms.app.App):
    '''
    Main app, extending rapidsms.app.App

    Overrides the handle and outgoing methods
    '''

    def handle(self, message):
        '''
        This will be called when messages come in. We don't return return
        anything, so as far as rapidsms is concerned, we haven't handled it
        so it just keeps passing it along to the latter apps.
        '''
        msg = LoggedMessage.create_from_message(message)
        msg.direction = LoggedMessage.DIRECTION_INCOMING
        msg.save()

        # Watermark the message object with the LoggedMessage pk.
        message.logger_id = msg.pk

        # Print message if debug
        self.debug(msg)


    def outgoing(self, message):
        '''
        This will be called when messages go out.
        '''
        
        msg = LoggedMessage.create_from_message(message)
        msg.direction = LoggedMessage.DIRECTION_OUTGOING

        # If an _outgoing_ message has a logger_id it is actually the logger_id
        # of the incoming message (because Message.respond does a copy.copy
        # on the message object). This is actually very convenient because
        # it allows us to match an outgoing message to the incoming message
        # that solicited it (assuming Message.respond) was used.
        if hasattr(message, 'logger_id'):
            try:
                orig_msg = LoggedMessage.incoming.get(pk=message.logger_id)
            except LoggedMessage.DoesNotExist:
                # Really no reason for this to ever happen, but if it does
                # we'll just silently continue, but we won't be able
                # to set the response_to field of this LoggedMessage
                pass
            else:
                # Set the response_to foreign key of this logged outgoing
                # message to the incoming message that it was copied from.
                msg.response_to = orig_msg
                # set status for incoming message
                orig_msg.status = msg.status
                orig_msg.save()

        msg.save()

        # Watermark the message object with the LoggedMessage pk.
        message.logger_id = msg.pk

        # Print message if debug
        self.debug(msg)
