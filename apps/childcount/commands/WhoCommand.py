#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from django.utils.translation import ugettext as _

from reporters.models import Reporter
from locations.models import Location

from childcount.commands import CCCommand
from childcount.models import CHW
from childcount.utils import authenticated


class WhoCommand(CCCommand):

    KEYWORDS = {
        'en': ['who'],
        'fr': ['qui'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        self.message.respond(
            _(u"You are registered as %(full_name)s from %(location)s with " \
               "alias @%(alias)s.") \
               % {'full_name': chw.full_name(), 'location': chw.location, \
                  'alias': chw.alias})

        return True
