#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
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


class StockOutCommand(CCCommand):

    KEYWORDS = {
        'en': ['stockout'],
        'rw': ['stockout'],
        'fr': ['stockout'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if self.params.__len__() < 3:
            raise ParseError(_(u"Not enough information. Expected:"
                                "%(keyword)s locationcode quantity" % \
                                {'keyword': self.params[0]}))
        try:
            loc = Location.objects.get(code__iexact=self.params[1])
        except Location.DoesNotExist:
            raise BadValue(_(u"Unknown location code %(loc)s." % \
                            {'loc': self.params[1]}))
        if not self.params[2].isdigit():
            raise BadValue(_(u"Bad Value for quantity %(val)s" % \
                            {'val': self.params[2]}))
        quantity = int(self.params[2])
        today = date.today()
        additional = u""
        try:
            bns = BednetStock.objects.get(created_on__day=today.day,
                                        created_on__month=today.month,
                                        created_on__year=today.year,
                                        location=loc)
        except BednetStock.DoesNotExist:
            self.message.respond(_(u"No Stockin for %(loc)s." % {'loc': loc}))
        else:
            if bns.start_point < quantity:
                self.message.respond(_(u"%(loc)s: %(q)s nets is greater than "
                                    " Starting point quantity %(sp)s nets."
                                    " Please check if your stock out quantity "
                                    "is correct." %\
                                    {'loc': loc, 'sp': bns.start_point,
                                    'q': quantity}))
            else:
                bns.chw = chw
                bns.end_point = quantity
                bns.save()
                self.message.respond(_(u"%(loc)s's closing stock is %(q)s nets"
                                "; Starting Point: %(sp)s; Issued: %(issued)s"
                                "" % {'loc': loc, 'sp': bns.start_point,
                                'q': quantity,
                                'issued': bns.start_point - bns.quantity}))
        return True
