#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.contrib.auth.models import User

import rapidsms

from findtb.utils import respond_exceptions, clean_msg
from findtb.exceptions import SMSException
from findtb.handlers import registration, unregister, mdrs


class App(rapidsms.app.App):

    @respond_exceptions
    def handle(self, message):
        message.text = clean_msg(message.text)

        # Don't process an empty message
        if not message.text:
            return False

        params = message.text.split()
        keyword = params.pop(0)

        if len(keyword) > 12:
            message.respond("Sorry, it looks like you forgot to put spaces " \
                            "in your message. Please separate all words and " \
                            "values with a space and send again.", 'error')
            return True

        keyword_dispatcher = {}

        modules = [registration, unregister, mdrs]
        keyword_dispatcher = {}
        for module in modules:
            for kw in module.KEYWORDS:
                keyword_dispatcher[kw] = module.handle

        if keyword in keyword_dispatcher:
            try:
                keyword_dispatcher[keyword](keyword, params, message)
            except SMSException, e:
                if hasattr(e, 'sms'):
                    message.respond(e.sms, 'error')
                return True
        else:
            message.respond("Sorry, %s is not a valid keyword. Please " \
                            "check the documentation and send again." % \
                             keyword.upper(), 'error')
        return True

