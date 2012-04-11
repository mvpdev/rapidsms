#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

import re

from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import ugettext as _
from django.db.models import Count

from checksum import checksum

from reporters.models import Reporter
from locations.models import Location
from childcount.models import HealthId

from childcount.commands import CCCommand
from childcount.models import Patient, CHW, Configuration
from childcount.models.PolioCampaignReport import PolioCampaignReport
from childcount.utils import authenticated, send_msg
from childcount.exceptions import CCException


class PolioSummaryCommand(CCCommand):

    KEYWORDS = {
        'en': ['plsummary', 'plsummery'],
        'fr': ['plsummary'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw
        try:
            phase = Configuration.get('polio_round')
        except Configuration.DoesNotExist:
            raise CCException(_(u"Configuration Error: Please contact system"
                                " administrator."))

        if PolioCampaignReport.objects.filter(patient__chw=chw, phase=phase):
            rpts = PolioCampaignReport.objects.filter(patient__chw=chw,
                                        patient__status=Patient.STATUS_ACTIVE,
                                                        phase=phase)
            count = rpts.count()
            dob = datetime.today() + relativedelta(months=-59)
            underfive = Patient.objects.filter(chw=chw, dob__gte=dob,
                                        status=Patient.STATUS_ACTIVE)
            total = underfive.count()
            percentage = 0
            if total:
                percentage = round((count / float(total)) * 100, 2)
            resp = _(u"Vaccinated: %(count)s of %(total)s - %(percentage)s%%" \
                    % {'count': count, 'total': total,
                        'percentage': percentage})
            self.message.respond(resp)
            not_covered = _(u"Not Vaccinated: ")
            not_covered_ids = []
            for rec in underfive.exclude(pk__in=rpts.values('patient'))[:20]:
                not_covered_ids.append(rec.health_id)
            if not_covered_ids:
                self.message.respond(not_covered + u", ".join(not_covered_ids))
            return True
        dob = datetime.today() + relativedelta(months=-59)
        underfive = Patient.objects.filter(dob__gte=dob,
                                    status=Patient.STATUS_ACTIVE)
        rpts = PolioCampaignReport.objects.filter(phase=phase)
        percentage = round((rpts.count() / float(underfive.count())) * 100, 2)
        resp = _(u"%(percentage)s%% coverage, Total Reports: %(total)s. " % \
                {'total': rpts.count(), 'percentage': percentage})
        rpts = rpts.values('chw__location__name', 'chw__location')\
                    .annotate(Count('chw'))
        for loc in rpts:
            loc_pk = loc['chw__location']
            t = underfive.filter(chw__location__pk=loc_pk).count()
            p = int(round((loc['chw__count'] / float(t)) * 100, 0))
            resp += u"%(loc)s: %(vacc)s/%(total)s - %(percentage)s%%. " % \
                    {'loc': loc['chw__location__name'],
                    'vacc': loc['chw__count'], 'total': t, 'percentage': p}
        self.message.respond(resp, 'success')
        if self.params.__len__() > 1 and self.params[1].lower() == 'all':
            for chw in CHW.objects.all():
                try:
                    send_msg(chw, resp)
                except:
                    pass
        return True
