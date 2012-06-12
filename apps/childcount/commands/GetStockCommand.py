#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from datetime import date

from django.utils.translation import ugettext as _

from reversion import revision
from reversion.models import Revision, Version

from locations.models import Location

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.utils import send_msg
from childcount.exceptions import BadValue, ParseError
from childcount.models import BednetStock


class GetStockCommand(CCCommand):

    KEYWORDS = {
        'en': ['getstock'],
        'rw': ['getstock'],
        'fr': ['getstock'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if self.params.__len__() < 2:
            raise ParseError(_(u"Not enough information. Expected:"
                                "%(keyword)s | locationcode |" % \
                                {'keyword': self.params[0]}))
        try:
            loc = Location.objects.get(code__iexact=self.params[1])
        except Location.DoesNotExist:
            raise BadValue(_(u"Unknown location code %(loc)s." % \
                            {'loc': self.params[1]}))
        today = date.today()
        try:
            bns = BednetStock.objects.get(created_on__day=today.day,
                                        created_on__month=today.month,
                                        created_on__year=today.year,
                                        location=loc)
        except BednetStock.DoesNotExist:
            self.message.respond(_(u"No Stockin for %(loc)s." % {'loc': loc}),
                                    'error')
        else:
            self.message.respond(_(u"%(loc)s: Starting Point: %(sp)s, "
                            "Balance: %(bal)s." % {'loc': loc,
                            'sp': bns.start_point,
                            'bal': bns.quantity}), 'success')
        return True
