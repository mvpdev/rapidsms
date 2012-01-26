#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

from datetime import datetime

import rapidsms
from rapidsms.parsers.keyworder import Keyworder
from rapidsms.connection import Connection
from rapidsms.message import Message

from upsmon.models import Event
from upsmon.utils import *


def str2bool(str_):
    ''' converts an sms-received bool (string) to actual boolean '''
    return str_.lower().strip() in ('true', 'yes', 'y')


def import_function(func):
    ''' import a function from full python path string.

    returns function.'''
    s = func.rsplit(".", 1)
    x = __import__(s[0], fromlist=[s[0]])
    f = eval("x.%s" % s[1])

    return f


class App (rapidsms.app.App):
    ''' UPS Monitor App

    sends notifications about power sources changes (off/on-line) '''

    keyword = Keyworder()

    def configure(self, enable='true', store='true', onevent='default', \
                  admin='', **extra):
        ''' define on notification behavior

        enable: whether or not to monitor ups (true|false)
        admin: name or number of reffering person
        store: whether to record events in DB (true|false)
        onevent: fqdn of function to execute or default or none
        default is childcount.utils.notify_admin
        **extra: any other key/value pair will be sent to function '''

        self.enable = str2bool(enable)
        self.store = str2bool(store)
        self.admin = admin.strip()
        self.extra = extra

        if onevent == 'default':
            self.callback = notify_admin
        else:
            self.callback = None

        try:
            self.callback = import_function(onevent)
        except:
            pass

    def parse(self, message):
        ''' tag message if there were sent by UPS Backend '''
        if message.connection.backend.slug == 'ups':
            message.from_ups = True

    def handle(self, message):
        ''' call appropriate function or pass '''
        # skip if config disabled app.
        if not self.enable:
            return False
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # no matching function
            return False
        try:
            self.handled = func(self, message, *captures)
        except Exception, e:
            self.handled = True
            message.respond(e)
            raise
        message.was_handled = bool(self.handled)
        return self.handled


    keyword.prefix = ''

    @keyword("((?:on|off)-line) (True|False) (\d+) (\d+) (True|False)")
    def notify(self, message, state, batt_pres, full_cap, cur_cap, request):
        ''' receives a  notification from UPS backend

        record the event into DB (if configured to)
        call configured function with Event message as param '''
        # we only want UPS originated messages
        if not message.from_ups:
            return False

        # sanitize input
        date = message.date
        device = message.connection.identity
        state = Event.STATE_ONLINE if state == 'on-line' \
                                   else Event.STATE_OFFLINE
        batt_pres = str2bool(batt_pres)
        full_cap = int(full_cap)
        cur_cap = int(cur_cap)
        request = str2bool(request)

        # create and save Event
        event = Event(device=device, date=date, state=state, \
                      battery_present=batt_pres, \
                      battery_full_capacity=full_cap, \
                      battery_current_capacity=cur_cap, \
                      requested=request)
        if self.store:
            event.save()


        self.callback(self, event, **self.extra)
        return True

    keyword.prefix = ''

    @keyword("ups(?:\s?)([a-z0-9\-]*)")
    def request(self, message, name):
        ''' respond to ups state refresh request

        sends a special message to UPS backend to request update '''
        # create message and forward to UPS backend
        # backend only respond to 'ups now'
        text = 'ups now'
        # default identity in case there is no history
        identity = 'BAT0'
        if name == '':
            # try to fetch last one received
            try:
                event = Event.objects.latest()
                identity = event.device
            except Event.DoesNotExist:
                pass
        else:
            identity = name.strip()

        # send to all UPS backends
        for backend in self._router.backends:
            if backend.slug != 'ups':
                continue
            c = Connection(backend, identity)
            msg = Message(connection=c, text=text, date=datetime.now())
            msg.send()

        return True
