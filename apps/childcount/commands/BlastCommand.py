#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

'''
    Broadcast message to all CHWs.
'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from reversion import revision
from reversion.models import Revision, Version

from childcount.models import CHW

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.utils import send_msg
from childcount.exceptions import Inapplicable


class BlastCommand(CCCommand):

    KEYWORDS = {
        'en': ['blast'],
        'rw': ['blast'],
        'fr': ['blast'],
    }

    @authenticated
    def process(self):
        print "Inside Blast Broadcaster"
        chw = self.message.persistant_connection.reporter.chw
        # TODO: limit reporters who can send this
        if self.params.__len__() > 1:
            msg = u' ' . join(self.params[1:])
            print u"Got message %s." % msg
            for chw in CHW.objects.all():
                send_msg(chw, msg)
