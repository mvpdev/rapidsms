#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from datetime import datetime, date, timedelta

from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group
from django.db.models import Sum

from reversion import revision
from reversion.models import Revision, Version

from locations.models import Location

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.utils import send_msg
from childcount.exceptions import BadValue, ParseError
from childcount.models import BednetStock, DistributionPoints
from childcount.models import BednetIssuedReport


class LLNSummaryCommand(CCCommand):

    KEYWORDS = {
        'en': ['netsummary'],
        'rw': ['netsummary'],
        'fr': ['netsummary'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw
        today = date.today()
        k = {}
        [k.update({dp.location: 0}) for dp in DistributionPoints.objects.all()]
        for bir in BednetIssuedReport\
            .objects\
            .filter(encounter__encounter_date__gte=today):
            d_sites = DistributionPoints.objects.filter(chw=bir.encounter.chw)
            distribution_site = None
            if d_sites:
                distribution_site = d_sites[0].location
            try:
                k[distribution_site] += bir.bednet_received
            except:
                print bir.encounter.chw
                continue

        _str = u''
        _jn = u''

        for item in k:
            try:
                bns = BednetStock.objects.get(created_on__day=today.day,
                    created_on__month=today.month,
                    created_on__year=today.year,
                    location=item)
            except BednetStock.DoesNotExist:
                continue
            remaining = bns.quantity
            print item, bns.quantity
            _str += _jn
            _str += u"%s:[start_point: %s, issued: %s, remaining: %s, "\
                "closing_point: %s]" % (item.__unicode__(),
                bns.start_point, k[item], remaining, bns.end_point)
            _jn = u', '
        if _str != '':
            self.message.respond(_str)
            # facilitators
            try:
                g = Group.objects.get(name='Facilitator')
                for user in g.user_set.all():
                    try:
                        send_msg(user.reporter, _str)
                    except:
                        print "Failed: ", user
            except Group.DoesNotExist:
                    pass
            for dp in DistributionPoints.objects.all():
                for chw in dp.chw.all():
                    try:
                        send_msg(chw, _str)
                    except:
                        print chw, _str
        if self.params.__len__() >= 2 and self.params[1].lower() == 'all':
            # for the campaign period
            start_date = datetime(2011, 2, 8)
            end_date = datetime(2011, 2, 11)
            current_date = start_date
            while current_date <= end_date:
                self._send_chw_net_summary(current_date)
                current_date = current_date + timedelta(1)
        else:
            self._send_chw_net_summary(today)
        return True

    def _send_chw_net_summary(self, dod):
        for dp in DistributionPoints.objects.all():
            for chw in dp.chw.all():
                inets = BednetIssuedReport.objects\
                    .filter(encounter__encounter_date__gte=dod,
                    encounter__chw=chw)\
                    .aggregate(dc=Sum('bednet_received'))
                if inets['dc']:
                    nets = inets['dc']
                else:
                    nets = 0
                msg = _(u"You issued %(n)s bednets on %(date)s") % \
                    {'n': nets, 'date': dod.strftime("%d/%m/%Y")}
                try:
                    send_msg(chw, msg)
                except:
                    print chw, msg
