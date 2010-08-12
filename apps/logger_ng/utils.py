#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
Helper utilities for logger_ng
'''

import urllib2
from urllib import urlencode

import rapidsms
from rapidsms.webui import settings

import config
from models import LoggedMessage

from direct_sms.utils import send_msg


def watermak(outgoing_message, in_response_to):
    """
        Inject the in the outgoing message id of the message we want to respond 
        to.
    """
    outgoing_message.logger_id = in_response_to
    outgoing_message.status = LoggedMessage.STATUS_LOGGER_RESPONSE


def respond_to_msg(msg, text):
    '''
    Sends a message to a reporter using the ajax app.  This goes to
    ajax_POST_send_message in direct_sms app.py and use a callback to 
    watermark the response.
    '''
    send_msg(backend=msg.backend, text=text, identity=msg.identity,
             callback=watermak, callback_kwargs={'in_response_to': msg.id})
             
