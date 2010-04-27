#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

import rapidsms

from findtb.utils import *
from findtb.handlers import RegistrationHandler

class App(rapidsms.app.App):
    keyworder = Keyworder()

    def start(self):
        pass

    @respond_exceptions
    def handle(self, message):
        message.text = clean_msg(message.text)

        # Don't process an empty message
        if not message.text:
            return False

        keyword = message.text.split()[0]

        if not self.keyworder.is_valid_keyword(keyword):
            message.respond("Sorry, %s is not a valid keyword. Please " \
                            "check the documentation and send again." % \
                             keyword.upper())
            return True
        function = self.keyworder.get_function(keyword)
        function(message)
        return True

    # Register users
    @keyworder('cli', 'dtu', 'dtls', 'ztl')
    def register(message):
        message.respond('registering')

    @keyworder('mdrs')
    @restricted
    def mdrs_registration(message):
        message.respond('mdrs registration')


    def cleanup(self):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing(self, message):
        """Handle outgoing message notifications."""
        pass

    def stop(self):
        """Perform global app cleanup when the application is stopped."""
        pass

