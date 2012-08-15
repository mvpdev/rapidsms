#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

from django.http import HttpResponse
from django.db.models import Count

from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.legends import Legend
from reportlab.lib import colors

from locations.models import Location

from childcount.models import PolioCampaignReport, Patient
from childcount.charts import CCBarChartDrawing, CCPieChartDrawing
from childcount.charts.utils import *


def polio_start_end_dates(phase):
    first_day = PolioCampaignReport.objects.filter(phase=phase)\
                                    .values('created_on')\
                                    .order_by('created_on')[0]['created_on']
    last_day = PolioCampaignReport.objects.filter(phase=phase)\
                                    .values('created_on')\
                                    .order_by('-created_on')[0]['created_on']
    return first_day, last_day


IMMUNIZATION_START_DATE = date(2010, 11, 24)


def daterange(start_date, end_date):
    end_date = end_date + timedelta(1)
    for n in range((end_date - start_date).days):
        yield start_date + timedelta(n)


def polio_piechart(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCPieChartDrawing(600, 600)
    start_date, end_date = polio_start_end_dates(phase)
    five_years_back = start_date + relativedelta(months=-59)
    tp = Patient.objects.filter(status=Patient.STATUS_ACTIVE,
                                    dob__gt=five_years_back).count()
    smdata = PolioCampaignReport.objects.filter(phase=phase,
                                patient__status=Patient.STATUS_ACTIVE)\
                                .values('chw__location__name',
                                        'chw__location')\
                                .order_by('chw__location__name')\
                                .annotate(Count('chw'))
    trpts = PolioCampaignReport.objects.filter(phase=phase,
                                patient__status=Patient.STATUS_ACTIVE).count()
    data = []
    cats = []
    count = 0
    tpercentage = 0
    for row in smdata:
        percentage = round((row['chw__count'] / float(tp)) * 100, 0)
        data.append(percentage)
        cats.append(u"%s - %s%%" % (row['chw__location__name'], percentage))
        count += row['chw__count']
        tpercentage += percentage
    data.append(100 - tpercentage)
    cats.append(u"Not Covered - %s%%" % (100 - tpercentage))
    d.add(String(10, d.chart.height + d.chart.y + 100,
                u"Polio Campaign Phase %s by sub-locaton - %s%% coverage:"
                "%s of %s reached." % (phase, tpercentage,
                count, tp)), name='title')
    d.title.fontSize = 18
    d.chart.data = data
    d.chart.labels = cats
    d.chart.xradius = 200

    d.chart.slices[0].fillColor = colors.steelblue
    d.chart.slices[1].fillColor = colors.thistle
    d.chart.slices[2].fillColor = colors.cornflower
    d.chart.slices[3].fillColor = colors.lightsteelblue
    d.chart.slices[4].fillColor = colors.aquamarine
    d.chart.slices[5].fillColor = colors.cadetblue
    d.chart.slices[6].fillColor = colors.lightcoral
    d.chart.slices[7].fillColor = colors.tan
    d.chart.slices[8].fillColor = colors.darkseagreen
    d.chart.slices[9].fillColor = colors.lemonchiffon
    d.chart.slices[10].fillColor = colors.lavenderblush
    d.chart.slices[11].fillColor = colors.lightgrey

    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                                        'polio-phase-%s-piechart' % phase)


def polio_percentage_barchart(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1280, 800)
    d.add(String(200, 780, u"Polio Campaign Report: Percentage Coverage "
            "Phase %s" % phase), name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 20
    start_date, end_date = polio_start_end_dates(phase)
    five_years_back = start_date + relativedelta(months=-59)
    smdata = PolioCampaignReport.objects.filter(phase=phase)\
                                        .values('chw__location__name',
                                        'chw__location')\
                                        .order_by('chw__location__name')\
                                        .annotate(Count('chw'))
    data = ()
    cats = []
    for row in smdata:
        c = row['chw__count']
        t = Patient.objects.filter(status=Patient.STATUS_ACTIVE,
                                    dob__gt=five_years_back,
                                    chw__location__pk=row['chw__location'])\
                                    .count()
        data += round(c / float(t) * 100, 0),
        cats.append(row['chw__location__name'])

    d.chart.data = [data]
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 10
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 100
    d.chart.x = 50
    d.chart.y = 50
    d.chart.width = d.chart.width - 20
    d.chart.height = d.chart.height - 100
    #d.chart.width = 400
    #d.chart.height = 400
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 18
    d.chart.barLabels.fontSize = 14
    d.chart.barLabelFormat = "%d%%"
    d.chart.barLabels.nudge = 10

    d.chart.bars[0].fillColor = colors.steelblue
    d.chart.bars[1].fillColor = colors.orange

    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                                        'polio-phase-%s-barchart' % phase)


def polio_percentage_comparison_barchart(request, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1280, 800)
    d.add(String(200, 780, u"Polio Campaign: Phase 1, Phase 2 and Phase 3"
                " Percentage Coverage Comparison"), name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 20
    data = []
    for phase in PolioCampaignReport.objects.values('phase')\
        .order_by('phase').distinct():
        start_date, end_date = polio_start_end_dates(phase['phase'])
        five_years_back = start_date + relativedelta(months=-59)
        smdata = PolioCampaignReport.objects.filter(phase=phase['phase'])\
                                            .values('chw__location__name',
                                            'chw__location')\
                                            .order_by('chw__location__name')\
                                            .annotate(Count('chw'))
        tdata = ()
        cats = []
        for row in smdata:
            c = row['chw__count']
            t = Patient.objects.filter(status=Patient.STATUS_ACTIVE,
                                    dob__gt=five_years_back,
                                    chw__location__pk=row['chw__location'])\
                                        .count()
            tdata += round(c / float(t) * 100, 0),
            cats.append(row['chw__location__name'])
        data.append(tdata)
    d.chart.data = data
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 10
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 100
    d.chart.x = 50
    d.chart.y = 50
    d.chart.width = d.chart.width - 20
    d.chart.height = d.chart.height - 100
    #d.chart.width = 400
    #d.chart.height = 400
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 18
    d.chart.barLabels.fontSize = 14
    d.chart.barLabelFormat = "%d%%"
    d.chart.barLabels.nudge = 10

    d.chart.bars[0].fillColor = colors.steelblue
    d.chart.bars[1].fillColor = colors.orange
    d.chart.bars[2].fillColor = colors.green

    legend = Legend()
    legend.alignment = 'left'
    legend.x = 100
    legend.y = d.chart.height + 100
    legend.dxTextSpace = 5
    legend.fontSize = 14
    legend.colorNamePairs = [(colors.steelblue, u"Phase 1"),
                            (colors.orange, u"Phase 2"),
                            (colors.green, u"Phase 3")]
    d.add(legend, 'legend')
    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                                        'polio-pcomparison-barchart')


def polio_malefemale_summary(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1280, 800)
    d.add(String(200, 700, u"Polio Campaign Phase %s: Daily "
                "Summary by Gender" % phase),
            name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 24
    start_date, end_date = polio_start_end_dates(phase)
    data = []
    for gender, s in Patient.GENDER_CHOICES:
        smdata = []
        cats = []
        for single_date in daterange(start_date, end_date):
            current_day = single_date
            next_day = single_date + timedelta(1)
            smdata.append({"count":
                PolioCampaignReport.objects.filter(created_on__gte=current_day,
                    created_on__lt=next_day, patient__gender=gender,
                    phase=phase).count()})
            cats.append(current_day.strftime("%A %d"))
        sdata = ()
        for row in smdata:
            sdata += row['count'],
        data.append(sdata)
    d.chart.data = data
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 100
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 1500
    d.chart.valueAxis.labels.fontSize = 18
    d.chart.x = 50
    d.chart.y = 50
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 20
    d.chart.barLabelFormat = "%d"
    d.chart.barLabels.nudge = 10
    d.chart.barLabels.fontSize = 14
    d.chart.barLabels.fontName = 'Helvetica-Bold'
    d.chart.barWidth = 150
    d.chart.bars[0].fillColor = colors.steelblue
    d.chart.bars[1].fillColor = colors.lemonchiffon
    d.chart.groupSpacing = 10
    legend = Legend()
    legend.alignment = 'left'
    legend.x = 100
    legend.y = 500
    legend.dxTextSpace = 5
    legend.fontSize = 14
    legend.colorNamePairs = [(colors.steelblue, u"Male"),
                            (colors.lemonchiffon, u"Female")]
    d.add(legend, 'legend')
    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                            'polio-malefemaleratio-phase-%s-barchart' % phase)


def daily_summary_per_location(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1440, 800)
    d.add(String(200, 700, u"Polio Campaign Phase %s: Daily summary by"
            " sub-locaton." % phase), name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 14
    start_date, end_date = polio_start_end_dates(phase)
    data = []
    for location in  \
        Location.objects.filter(type__name='Sub Location')\
            .order_by('name'):
        smdata = []
        cats = []
        for single_date in daterange(start_date, end_date):
            current_day = single_date
            next_day = single_date + timedelta(1)
            smdata.append({"location": location,
                        "count":
                PolioCampaignReport.objects.filter(created_on__gte=current_day,
                    created_on__lt=next_day,
                    phase=phase,
                    patient__chw__location=location).count()})
            cats.append(current_day.strftime("%A %d"))
        sdata = ()
        for row in smdata:
            sdata += row['count'],
        data.append(sdata)
    d.chart.data = data
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 50
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 800
    d.chart.valueAxis.labels.fontSize = 18
    d.chart.x = 30
    d.chart.y = 50
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 18
    d.chart.barLabels.fontSize = 14
    d.chart.barLabelFormat = "%d"
    d.chart.barLabels.nudge = 10
    d.chart.barWidth = 10
    d.chart.groupSpacing = 5

    d.chart.bars[0].fillColor = colors.steelblue
    d.chart.bars[1].fillColor = colors.thistle
    d.chart.bars[2].fillColor = colors.cornflower
    d.chart.bars[3].fillColor = colors.lightsteelblue
    d.chart.bars[4].fillColor = colors.aquamarine
    d.chart.bars[5].fillColor = colors.cadetblue
    d.chart.bars[6].fillColor = colors.lightcoral
    d.chart.bars[7].fillColor = colors.tan
    d.chart.bars[8].fillColor = colors.darkseagreen
    d.chart.bars[9].fillColor = colors.lemonchiffon
    d.chart.bars[10].fillColor = colors.lavenderblush

    legend = Legend()
    legend.alignment = 'left'
    legend.x = 100
    legend.y = 500
    legend.dxTextSpace = 5
    legend.fontSize = 14
    legend.deltax = 150
    legend.variColumn = False
    legend.colorNamePairs = [(colors.steelblue, u"Anyiko"),
                            (colors.thistle, u"Gongo"),
                            (colors.cornflower, u"Jina"),
                            (colors.lightsteelblue, u"Lihanda"),
                            (colors.aquamarine, u"Marenyo"),
                            (colors.cadetblue, u"Nyamninia"),
                            (colors.lightcoral, u"Nyandiwa"),
                            (colors.tan, u"Nyawara"),
                            (colors.darkseagreen, u"Ramula"),
                            (colors.lemonchiffon, u"Sauri"),
                            (colors.lavenderblush, u"Uranga")]
    d.add(legend, 'legend')
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                'polio-dailysummary-per-location-phase-%s-barchart' % phase)


def polio_daily_summary(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1280, 800)
    d.add(String(200, 700, u"Polio Campaign Phase %s: Daily summary" % phase),
                name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 24
    start_date, end_date = polio_start_end_dates(phase)
    data = []
    smdata = []
    cats = []
    for single_date in daterange(start_date, end_date):
        current_day = single_date
        next_day = single_date + timedelta(1)
        smdata.append({"count":
            PolioCampaignReport.objects.filter(created_on__gte=current_day,
                                phase=phase, created_on__lt=next_day).count()})
        cats.append(current_day.strftime("%A %d"))
    sdata = ()
    for row in smdata:
        sdata += row['count'],
    data.append(sdata)
    d.chart.data = data
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 100
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 3000
    d.chart.valueAxis.labels.fontSize = 18
    d.chart.x = 50
    d.chart.y = 50
    #d.chart.width = 400
    #d.chart.height = 400
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 20
    d.chart.barLabelFormat = "%d"
    d.chart.barLabels.nudge = 10
    d.chart.barLabels.fontSize = 14
    d.chart.barLabels.fontName = 'Helvetica-Bold'
    d.chart.barWidth = 150
    d.chart.bars[0].fillColor = colors.steelblue
    d.chart.groupSpacing = 10
    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                            'polio-dailysummary-phase-%s-barchart' % phase)


def polio_daily_summary_comparison(request, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1280, 800)
    d.add(String(200, d.chart.height, u"Polio Campaign Report: Daily summary"),
                name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 24
    data = []
    rows = []
    for phase in PolioCampaignReport.objects.values('phase')\
        .order_by('phase').distinct():
        start_date, end_date = polio_start_end_dates(phase['phase'])
        smdata = []
        cats = []
        day = 0
        for single_date in daterange(start_date, end_date):
            current_day = single_date
            next_day = single_date + timedelta(1)
            day += 1
            smdata.append(
                PolioCampaignReport.objects.filter(created_on__gte=current_day,
                                            phase=phase['phase'],
                                            created_on__lt=next_day).count())
            cats.append(u"Day %d" % day)
        rows.append(smdata)
    if rows[0].__len__() > rows[1].__len__():
        rows[1].extend([0] * (rows[0].__len__() - rows[1].__len__()))
    else:
        rows[0].extend([0] * (rows[1].__len__() - rows[0].__len__()))
    for row in rows:
        sdata = ()
        for item in row:
            sdata += item,
        data.append(sdata)
    d.chart.data = data
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 100
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 3000
    d.chart.valueAxis.labels.fontSize = 18
    d.chart.x = 50
    d.chart.y = 50
    #d.chart.width = 400
    #d.chart.height = 400
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 20
    d.chart.barLabelFormat = "%d"
    d.chart.barLabels.nudge = 10
    d.chart.barLabels.fontSize = 14
    d.chart.barLabels.fontName = 'Helvetica-Bold'
    d.chart.barWidth = 150
    d.chart.bars[0].fillColor = colors.steelblue
    d.chart.bars[1].fillColor = colors.lemonchiffon
    d.chart.bars[2].fillColor = colors.green
    d.chart.groupSpacing = 10
    legend = Legend()
    legend.alignment = 'left'
    legend.x = 100
    legend.y = d.chart.height - 10
    legend.dxTextSpace = 5
    legend.fontSize = 14
    legend.colorNamePairs = [(colors.steelblue, u"Phase 1"),
                            (colors.lemonchiffon, u"Phase 2"),
                            (colors.green, u"Phase 3")]
    d.add(legend, 'legend')
    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                            'polio-dailysummary-comparison-barchart')


def polio_locations_piechart(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCPieChartDrawing(1280, 800)
    smdata = PolioCampaignReport.objects.filter(phase=phase)\
                                        .values('chw__location__name',
                                        'chw__location').annotate(Count('chw'))
    data = []
    cats = []
    count = PolioCampaignReport.objects.filter(phase=phase).count()
    for row in smdata:
        data.append(row['chw__count'])
        percentage = round((row['chw__count'] / float(count)) * 100, 2)
        cats.append(u"%s - %s - %s%%" % (row['chw__location__name'],
            row['chw__count'], percentage))
    d.add(String(200, d.chart.height + 100, u"Polio Campaign Phase %s by "
            "sub-locaton: %s total reports" % (phase, count)), name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 24
    d.chart.data = data
    d.chart.labels = cats
    d.chart.xradius = 400
    d.chart.yradius = 280
    d.chart.x = 50
    d.chart.slices.fontSize = 18

    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                            'polio-locations-phase-%s-piechart' % phase)


def polio_locations_barchart(request, phase=1, cformat='png'):
    #instantiate a drawing object
    d = CCBarChartDrawing(1280, 800)
    d.add(String(200, d.chart.height + 100, 'Polio Campaign Phase %s' % phase),
                name='title')
    d.title.fontName = 'Helvetica-Bold'
    d.title.fontSize = 20
    smdata = PolioCampaignReport.objects.filter(phase=phase)\
                                        .values('chw__location__name',
                                        'chw__location')\
                                        .order_by('chw__location__name')\
                                        .annotate(Count('chw'))
    data = ()
    cats = []
    for row in smdata:
        data += row['chw__count'],
        cats.append(row['chw__location__name'])

    d.chart.data = [data]
    d.chart.categoryAxis.categoryNames = cats
    d.chart.valueAxis.valueStep = 100
    d.chart.valueAxis.valueMin = 0
    d.chart.valueAxis.valueMax = 1600
    d.chart.x = 50
    d.chart.y = 150
    d.chart.width = d.chart.width - 20
    #d.chart.width = 400
    #d.chart.height = 400
    d.chart.categoryAxis.labels.boxAnchor = 's'
    d.chart.categoryAxis.labels.angle = 0
    d.chart.categoryAxis.labels.dy = -25
    d.chart.categoryAxis.labels.fontSize = 18
    d.chart.barLabels.fontSize = 14
    d.chart.barLabelFormat = "%d"
    d.chart.barLabels.nudge = 10

    d.chart.bars[0].fillColor = colors.steelblue

    #get a GIF (or PNG, JPG, or whatever)
    binaryStuff = d.asString(cformat.lower())
    return render_chart_to_response(request, binaryStuff, cformat.lower(),
                            'polio-locations-phase-%s-barchart' % phase)
