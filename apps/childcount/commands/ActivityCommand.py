#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from reversion import revision
from reversion.models import Revision, Version
from childcount.models.ccreports import TheCHWReport

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.exceptions import Inapplicable


class ActivityCommand(CCCommand):

    KEYWORDS = {
        'en': ['activity'],
        'fr': ['activity'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        thechw = TheCHWReport.objects.get(id=chw.id)
        summary = thechw.activity_summary()
        self.message.respond(_(u"This week(%(sdate)s -%(edate)s): " \
                                "%(numhvisit)d household visit, %(muac)d " \
                                "MUAC(%(severemuac)d SAM/MAM) %(rdt)d RDT. You " \
                                "have %(household)d households, %(ufive)d " \
                                "under five, %(tclient)d total registerd " \
                                "clients") % summary)
