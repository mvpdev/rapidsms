#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' forward incoming messages from PIPE backend

    messages must comply to following format:
    destination:message

    aliases can be configured in local.ini '''

import re
from datetime import datetime

import rapidsms
from rapidsms.connection import Connection
from rapidsms.message import Message


class App (rapidsms.app.App):

    ''' message forwarding from PIPE backend to other ones '''

    def configure(self, **recipients):
        ''' registers aliases from local.ini file

        register as many alias you want in local.ini
        Examples:
        admin=+123456908 '''
        self.recipients = recipients

    def handle(self, message):
        ''' forward messages to all backends

        filter messages from PIPE backend which follows format
        forward message to appropriate recipient through all backends '''

        # we only want PIPE sent message
        matchs = re.match(r'^(?P<dest>[\+\-\_a-zA-Z0-9]+)\:.*$', message.text)
        if message.connection.backend.slug == 'pipe' and matchs:

            # retrieve destination from message
            dest = matchs.groupdict()['dest']

            # try to match an alias from configuration
            if dest in self.recipients:
                identity = self.recipients[dest]
            else:
                identity = dest

            # message is next to recipient
            text = message.text.split(':', 1)[1]

            # send the message to all backends
            for backend in self._router.backends:
                c = Connection(backend, identity)
                msg = Message(connection=c, text=text, date=datetime.now())
                msg.send()

            return True
        else:
            return False
