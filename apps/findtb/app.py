#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.contrib.auth.models import User

import rapidsms

from locations.models import Location
from reporters.models import Reporter
from findtb.utils import *
from findtb.exceptions import SMSException
from findtb.models import *
from findtb.handlers import registration


class App(rapidsms.app.App):

    @respond_exceptions
    def handle(self, message):
        message.text = clean_msg(message.text)

        # Don't process an empty message
        if not message.text:
            return False

        params = message.text.split()
        keyword = params.pop(0)

        keyword_dispatcher = {}
        for kw in registration.KEYWORDS:
            keyword_dispatcher[kw] = registration.handle

        if keyword in keyword_dispatcher:
            try:
                keyword_dispatcher[keyword](keyword, params, message)
            except SMSException, e:
                message.respond(e.sms, 'error')
                return True
        else:
            message.respond("Sorry, %s is not a valid keyword. Please " \
                            "check the documentation and send again." % \
                             keyword.upper(), 'error')
        return True

