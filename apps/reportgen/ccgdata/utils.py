#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import datetime
import bonjour

from django.utils.translation import ugettext as _

from rapidsms.webui import settings

from reportgen.timeperiods import TwelveMonths
from reportgen.timeperiods import ThirteenWeeks
from reportgen.definitions.VitalEventsReport import ReportDefinition as \
                                                        VEsReportDefinition

from reportgen.ccgdata import CCGData


def update_header_vital_events_worksheet(ccgdata, key, wksht_id, time_period):
    if not isinstance(ccgdata, CCGData):
        raise Exception(_(u'ccgdata is not an instance of CCGData.'))
    title = u"%s: %s" % (VEsReportDefinition.title, time_period.title)
    ccgdata.cellsUpdateAction(key, wksht_id, 2, 1, title)
    headers = ["Indicator"]
    # a time period creates the headers i.e Year Month e.g 2011 September
    headers.extend([bonjour.dates.format_date(p.start, "Y MMMM") for p in \
                    time_period.sub_periods()])
    row = 3
    for i in range(1, headers.__len__() + 1):
        col = i
        print headers[i - 1]
        ccgdata.cellsUpdateAction(key, wksht_id, row, col, headers[i - 1])


def update_header_13Wvital_events_worksheet(ccgdata, key, wksht_id, time_period):
    if not isinstance(ccgdata, CCGData):
        raise Exception(_(u'ccgdata is not an instance of CCGData.'))
    title = u"%s: %s" % (VEsReportDefinition.title, time_period.title)
    ccgdata.cellsUpdateAction(key, wksht_id, 2, 1, title)
    headers = ["Indicator"]
    # a time period creates the headers i.e Year Month e.g 2011 September
    headers.extend([u"%s to %s" % \
        (bonjour.dates.format_date(p.start, "d MMMM"), \
        bonjour.dates.format_date(p.end, "d MMMM")) for p in \
                    time_period.sub_periods()])
    row = 3
    for i in range(1, headers.__len__() + 1):
        col = i
        print headers[i - 1]
        ccgdata.cellsUpdateAction(key, wksht_id, row, col, headers[i - 1])


def default_vital_events_worksheet(ccgdata, key, wksht_id):
    if not isinstance(ccgdata, CCGData):
        raise Exception(_(u'ccgdata is not an instance of CCGData.'))
    # headers
    update_header_vital_events_worksheet(ccgdata, key, wksht_id)
    # indicators
    indicators = [unicode(ind.short_name) for ind in \
                                            VEsReportDefinition._indicators]

    col = 1
    for i in range(1, indicators.__len__()):
        row = i + 3
        ccgdata.cellsUpdateAction(key, wksht_id, row, col, indicators[i - 1])


def update_vital_events_worksheet(ccgdata, key, wksht_id, data):
    if not isinstance(ccgdata, CCGData):
        raise Exception(_(u'ccgdata is not an instance of CCGData.'))

    for i in range(1, data.__len__() + 1):
        row = i + 3
        rowdata = data[i - 1]
        for col in range(1, rowdata.__len__() + 1):
            ccgdata.cellsUpdateAction(key, wksht_id, row, col, \
                str(rowdata[col - 1]))


def set_progress(ccgdata, key, wksht_id, status):
    '''Use the first cell to indicate progress and/or last updated time'''
    row = col = 1
    ccgdata.cellsUpdateAction(key, wksht_id, row, col, unicode(status))


def update_vital_events_report():
    conf = settings.RAPIDSMS_APPS["reportgen"]
    username = conf["gdata.username"]
    password = conf["gdata.password"]
    key = conf["gdata.last12monthskey"]
    site= conf["gdata.site"]

    ccgdata = CCGData()

    try:
        ccgdata.login(username, password)
    except Exception:
        raise Exception(_(u'Error: Unable to login to google docs'))
    else:
        wksht_id = ccgdata.createWorksheet(key, site)
        # default_vital_events_worksheet(ccgdata, key, wksht_id)

        last12months = TwelveMonths._twelvemonth_period(0)
        # headers
        update_header_vital_events_worksheet(ccgdata, key, wksht_id, \
                                            last12months)
        # indicators
        data = VEsReportDefinition.data_only(last12months)

        # updating progress
        set_progress(ccgdata, key, wksht_id, _(u'Update in progress'))

        update_vital_events_worksheet(ccgdata, key, wksht_id, data)

        # updating progress
        now = datetime.datetime.now()
        last_update = bonjour.dates.format_datetime(now, "full")
        set_progress(ccgdata, key, wksht_id, _(u'Last Update @ %(now)s' % \
                                            {'now': last_update}))


def update_13Wvital_events_report():
    conf = settings.RAPIDSMS_APPS["reportgen"]
    username = conf["gdata.username"]
    password = conf["gdata.password"]
    key = conf["gdata.last13weekskey"]
    site= conf["gdata.site"]

    ccgdata = CCGData()

    try:
        ccgdata.login(username, password)
    except Exception:
        raise Exception(_(u'Error: Unable to login to google docs'))
    else:
        wksht_id = ccgdata.createWorksheet(key, site)
        # default_vital_events_worksheet(ccgdata, key, wksht_id)

        time_p = ThirteenWeeks._thirteenweek_period(0)
        # headers
        update_header_13Wvital_events_worksheet(ccgdata, key, wksht_id, time_p)
        # indicators
        data = VEsReportDefinition.data_only(time_p)

        # updating progress
        set_progress(ccgdata, key, wksht_id, _(u'Update in progress'))

        update_vital_events_worksheet(ccgdata, key, wksht_id, data)

        # updating progress
        now = datetime.datetime.now()
        last_update = bonjour.dates.format_datetime(now, "full")
        set_progress(ccgdata, key, wksht_id, _(u'Last Update @ %(now)s' % \
                                            {'now': last_update}))
