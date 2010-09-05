#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.contrib.auth.models import User

import rapidsms

from reporters.models import Reporter
from findtb.libs.utils import respond_exceptions, clean_msg
from findtb.exceptions import SMSException
from findtb.handlers import registration, unregister, tsrs, eqa, notice

#TODO: when creating a new specimen, if it's a replacment, set the replacement
# in the previous one

class App(rapidsms.app.App):

    def ajax_POST_send_message(self, urlparser, post):
        """
        Callback method for sending messages from the webui via the ajax app.
        """
        rep = Reporter.objects.get(pk=post["reporter"])
        pconn = rep.connection()

        # abort if we don't know where to send the message to
        # (if the device the reporter registed with has been
        # taken by someone else, or was created in the WebUI)
        if pconn is None:
            raise Exception("%s is unreachable (no connection)" % rep)

        # attempt to send the message
        # TODO: what could go wrong here?
        be = self.router.get_backend(pconn.backend.slug)
        return be.message(pconn.identity, post["text"]).send()

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

        modules = [registration, unregister, tsrs, eqa, notice]
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

