#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

import re

from django.utils.translation import ugettext as _

from datetime import datetime
from datetime import timedelta

from reporters.models import Reporter
from locations.models import Location

from alerts.utils import SmsAlert

from childcount.commands import CCCommand
from childcount.models import CHW
from childcount.utils import authenticated
from childcount.exceptions import BadValue, ParseError


class TestAlertsCommand(CCCommand):

    KEYWORDS = {
        'en': ['alert'],
        'rw': ['alert'],
        'fr': ['alert'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if self.params.__len__() < 4:
            raise ParseError(_(u"alert command requires | username |" \
                                " delay[s/m/h) | message"))
            return True
        username = self.params[1].lower()
        try:
            chw = CHW.objects.get(username__iexact=username)
        except Reporter.DoesNotExist:
            raise BadValue(_(u"No patient with health id %(health_id)s") \
                                    % {'health_id': health_id})
        else:
            delay = self.params[2]
            t = 's'
            if not delay.isdigit():
                t = delay[len(delay) - 1]
                delay = delay[: len(delay) - 1]
                if not delay.isdigit() or t.lower() not in ('s', 'm', 'h'):
                    raise ParseError(_(u"Could not understand %(error)s" \
                        " delay.") % {'error': self.params[2]})
                    return True
            try:
                delay = int(delay)
            except ValueError:
                raise  BadValue(_(u"Could not understand %(error)s delay" \
                                    % {'error': self.params[2]}))
            else:
                send_at = datetime.now()
                if t == 's':
                    send_at = send_at + timedelta(seconds=delay)
                elif t == 'm':
                    send_at = send_at + timedelta(minutes=delay)
                elif t == 'h':
                    send_at = send_at + timedelta(hours=delay)
                else:
                    send_at = send_at + timedelta(seconds=delay)
                msg = u"%s> %s" % (self.message.reporter, \
                                    ' '. join(self.params[3:]))
                alert = SmsAlert(reporter=chw, msg=msg)
                am = alert.send(send_at=send_at)
                self.message.respond(_(u"%(chw)s will be notified at" \
                                        " %(time)s") % \
                                {'chw': chw, \
                                'time': send_at})
        return True
