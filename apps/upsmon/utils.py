#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

from datetime import datetime

from rapidsms.connection import Connection
from rapidsms.message import Message

from upsmon.models import Event


def notify_admin(app, event, **extra):
    ''' send a textual notification of event to admin '''

    identity = app.admin
    if identity is None:
        return False

    # build message from Event's verbose method
    text = event.verbose()

    # send message through all backends
    for backend in app._router.backends:
        c = Connection(backend, identity)
        msg = Message(connection=c, text=text, date=datetime.now())
        msg.send()
