#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import os
import operator
from datetime import date, datetime, timedelta
from cStringIO import StringIO
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from time import localtime

from django.utils.translation import ugettext as _
from django.test import client

from matplotlib import use as mpl_use
mpl_use('PDF')
import matplotlib.pyplot as pyplot
import matplotlib.dates as mpl_dates
from matplotlib.font_manager import FontProperties
from pylab import NaN

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, Paragraph, Frame

import xlwt

from rapidsms import Message
from rapidsms.connection import *
from apps.reporters.models import *
from apps.findug.models import *


def diseases_from_string(text):

    """
    Accepts a string (from SMS) of the diseases.  ie:
        ma76 dy72+2 ch1

    Returns a list of dictionaries of the diseases.  For example, with the
    above example disease string, the return would be:
        [{'cases': 76, 'disease': <Disease: Malaria>, 'deaths': 0},
         {'cases': 72, 'disease': <Disease: Dysentery>, 'deaths': 2},
         {'cases': 1, 'disease': <Disease: Cholera>, 'deaths': 0}]
    """

    diseases = []

    # split different diseases declarations
    codes = text.split(' ')

    for code in codes:
        if code == '':
            continue
        try:
            # extract values: <CODE><CASES#>+<DEATHS>
            re_string = '([a-zA-Z]+)([0-9]+)\+?([0-9]*)'
            extract = re.search(re_string, code).groups()
            abbr = extract[0].lower()
            cases = int(extract[1])
            deaths = 0 if extract[2].__len__() == 0 else int(extract[2])
        except:
            raise InvalidInput

        try:
            disease = Disease.by_code(abbr)
        except Disease.DoesNotExist:
            raise IncoherentValue(_(u"FAILED: %s is not a valid disease code. "
                                     "Please try again.") % abbr)

        diseases.append({'disease': disease, 'cases': cases, 'deaths': deaths})

    return diseases


def send_reminder(router, *args, **kwargs):

    """
    Sends a reminder to all health workers that are registered with health
    units that have completed the EpidemiologicalReport for the week.

    It only send to health workers for whom regestered_self == True.
    Any health worker who has sent PAUSE or STOP should have
    regestered_self = False, so they won't receive the reminders.

    Raised by the scheduler.
    """

    health_units = HealthUnit.objects.all()
    health_units = filter(lambda hu: hu.reporters.count() > 0, health_units)
    current_period = ReportPeriod.current()
    for hu in health_units:
        completed = EpidemiologicalReport.STATUS_COMPLETED
        reps = EpidemiologicalReport.objects.filter(_status=completed)
        if reps.filter(clinic=hu, period=current_period).count() == 0:
            for reporter in hu.reporters.filter(registered_self=True,
                                                role__code='hw'):
                try:
                    b = router.get_backend(reporter.connection().backend.slug)
                    if b:
                        connection = Connection(b,
                                                reporter.connection().identity)
                        message = Message(connection=connection)
                        message.text = _(u"You have not completed your weekly "
                                          "report for %(health_unit)s. Please "
                                          "send your reports as soon as "
                                          "possible. Thank you.") % \
                                          {'health_unit': hu}
                        message.send()
                except Exception, e:
                    print _(u"Can't send reminder to %(rec)s: %(err)s") % \
                             {'rec': reporter, 'err': e}


def cb_disease_alerts(router, *args, **kwargs):

    """
    Sends alerts from DiseaseAlert objects to reporters.

    Raised by the scheduler.
    """

    # retrieve unsent alerts
    alerts = DiseaseAlert.objects.filter(status=DiseaseAlert.STATUS_STARTED)

    for alert in alerts:

        alert_msg = _(u"ALERT. At least %(nbcases)s cases of %(disease)s "
                       "in %(location)s during %(period)s") % \
                       {'nbcases': alert.value,
                        'disease': alert.trigger.disease,
                        'location': alert.trigger.location,
                        'period': alert.period}

        for reporter in list(alert.recipients.all()):

            try:
                back = router.get_backend(reporter.connection().backend.slug)
                if back:
                    connection = Connection(back,
                                            reporter.connection().identity)
                    message = Message(connection=connection)
                    message.text = alert_msg
                    message.send()
            except Exception, e:
                print _(u"Can't send alert to %(rec)s: %(err)s") % \
                         {'rec': reporter, 'err': e}

        # change alert status
        alert.status = DiseaseAlert.STATUS_COMPLETED
        alert.save()


def report_completed_alerts(router, report):

    """
    Called by app.py whenever an EpidemiologicalReport is complete.

    Sends a summary report to any reporter in that location (or one
    of its decendents) that is in the group 'weekly_completion_alerts'
    and has self_regestered = True
    """

    # verify report is done
    if not report.status == EpidemiologicalReport.STATUS_COMPLETED:
        return False

    # get sub districts
    targets = []
    for ancestor in report.clinic.ancestors():
        if ancestor.type.name.lower().__contains__('health sub district'):
            targets.append(ancestor)

    # get reporters
    recipients = []
    reporters = Reporter.objects.filter(registered_self=True,
                                        location__in=targets)
    for reporter in reporters:
        if ReporterGroup.objects.get(title='weekly_completion_alerts') in \
           reporter.groups.only():
            recipients.append(reporter)

    # send alerts
    alert_header = _(u"%(clinic)s report: " % {'clinic': report.clinic})

    alert_msg = "%s %s %s" % (alert_header, report.diseases.summary,
                              report.act_consumption.sms_stock_summary)
    if report.remarks:
        alert_msg = "%s Remarks: %s" % (alert_msg, report.remarks)

    for recipient in recipients:
        try:
            back = router.get_backend(recipient.connection().backend.slug)
            if back:
                connection = Connection(back,
                                        recipient.connection().identity)
                message = Message(connection=connection)
                message.text = alert_msg
                message.send()
        except Exception, e:
            print _(u"Can't send alert to %(rec)s: %(err)s") % \
                    {'rec': recipient, 'err': e}


def create_excel(context_dict):

    """
    Creates an Excel document of a report.

    It accepts one argument, the context_dict from views.report_view.

    It returns a string of data containing the Excel document, which can
    be written to a response.
    """

    header_style = xlwt.XFStyle()
    header_style.font.bold = True
    header_style.font.height = 160
    header_style.alignment.horz = xlwt.Alignment.HORZ_CENTER
    header_style.alignment.wrap = xlwt.Alignment.WRAP_AT_RIGHT

    normal_style = xlwt.XFStyle()

    PINK = 14
    incomplete_style = xlwt.XFStyle()
    incomplete_style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    incomplete_style.pattern.pattern_fore_colour = PINK

    wb = xlwt.Workbook()
    ws = wb.add_sheet(context_dict['report_title'])
    ws.row(0).height = 420
    c = 0
    for column in context_dict['columns']:
        if context_dict['sub_columns']:
            if not 'colspan' in column:
                ws.write_merge(0, 1, c, c, column['name'], header_style)
            else:
                ws.write_merge(0, 0, c, c + column['colspan'] - 1,
                               column['name'], header_style)
                c += column['colspan'] - 1
        else:
            ws.write(0, c, column['name'], header_style)
        c += 1

    cases_deaths = lambda value: re.sub(r'^C$', 'Cases',
                                        re.sub(r'^D$', 'Deaths', value))
    if context_dict['sub_columns']:
        c = 1
        for sub_column in context_dict['sub_columns']:
            ws.write(1, c, cases_deaths(sub_column['name']), header_style)
            c += 1
        r = 2
    else:
        r = 1

    for row in context_dict['rows']:
        style = normal_style if row['complete'] else incomplete_style
        c = 0
        for cell in row['cells']:
            ws.write(r, c, cell['value'], style)
            c += 1
        r += 1

    temp_buffer = StringIO()
    wb.save(temp_buffer)
    return temp_buffer.getvalue()


def email_report(router, recipient, report):

    email_backend = router.get_backend('email')
    if not email_backend:
        return True
    if len(recipient.connections.filter(backend__slug=email_backend.slug)) == \
                                                                             0:
        return True
    connection = Connection(email_backend,
                            recipient.connections.get(
                                  backend__slug=email_backend.slug).identity)

    message = Message(connection=connection)
    c = client.Client()
    message_lines = []
    message_lines.append('From: hmis@findug.buildafrica.org')
    message_lines.append('Subject: Weekly report from %s' % report.clinic)
    message_lines.append('')
    begin = False
    for line in str(c.get('/findug/epidemiological_report/%d' % report.id)) \
                                                                .split('\n'):
        if not begin and line.lower().find('<html') != -1:
            begin = True
        if begin:
            message_lines.append(line)
    message.text = '\n'.join(message_lines)
    try:
        message.send()
    except Exception, e:
        print _(u"Can't send email to %(rec)s: %(err)s") % \
                {'rec': recipient, 'err': e}


def merge_pdfs(background, stamp, *args):

    """
    Merges multple pdfs together.
    args -  The function takes two or more arguments of pdfs. Each arg can
            be a string containing a file path for a pdf i.e. '/data/my.pdf'
            or it can be a StringIO object containing the pdf data.

    Returns a StringIO object containing the merged pdfs

    Note:   If it doesn't seem to work, check whether your pdf has a
            transparent background- if it doesn't, it will cover all layers
            below.  The PDFs should be the same dimmensions.

    Note:   The pdfs are stacked in the order in which they are passed.
            i.e: merge_pdfs('backlayer.pdf','nextlayer.pdf',top_layer_obj)
    """

    # recursion
    if len(args) > 0:
        return merge_pdfs(merge_pdfs(background, stamp, *args[:-1]), args[-1])

    if len(args) == 0:
        # a simple test to see if the arg is a buffer
        is_buffer = lambda arg: isinstance(arg, type(StringIO()))

        # we can't pass two different pipes to pdftk, so if neither arg is a
        #   filename we need to write one to a temporary file.
        temp_file = False
        if is_buffer(background) and is_buffer(stamp):
            temp_file = NamedTemporaryFile()
            temp_file.write(background.getvalue())
            temp_file.flush()
            background = temp_file.name

        # Now either the background or stamp (or both) MUST be a file object.
        #   If one is still a buffer, set it up so we can pipe it into pdftk.
        pdf_buffer = False
        if is_buffer(background):
            pdf_buffer = background
            background = '-'
        elif is_buffer(stamp):
            pdf_buffer = stamp
            stamp = '-'

        args = ['/usr/bin/pdftk', background, 'stamp', stamp, 'output', '-']
        proc = Popen(args, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        if pdf_buffer: # one is a buffer, so we need to pipe it in
            pdf, cmderr = proc.communicate(pdf_buffer.getvalue())
            pdf_buffer.close()

        else: # they are both file paths, so we don't have a buffer to pass
            pdf, cmderr = proc.communicate()

        # don't forget to close the temp_file if we created one. This will also
        #   delete it from the computer
        if temp_file:
            temp_file.close()

        return_buffer = StringIO()
        return_buffer.write(pdf)

        return return_buffer


class LinePlot():

    """ My documentation """

    MARKERS = ['o', 's', '^', 'd', 'p', '>', 'h',
               'v', '*', '<', 'H', '1', '2', '3', '4']
    COLORS = ['#00006b', '#ebeb00', '#ff0505',
              '#00eb4e', '#9e4f00', '#00a0f0',
              '#005c3d', '#610061', '#ff8fc7',
              '#000000']
    marker_size = 5
    line_width = 1
    ypad_percentage = 5
    xpad_percentage = 2
    axis_label_font_size = 8
    tick_font_size = 7
    legend_font_size = 8
    grid = True
    page_width = 29.7
    page_height = 21.0
    xaxis_label_height = 0.7
    yaxis_label_width = 1.1

    def __init__(self, title, fig_width, fig_height, fig_left, fig_top):
        self.figure_title = title
        self.fig_width = fig_width
        self.fig_height = fig_height
        self.fig_left = fig_left
        self.fig_top = fig_top
        self.periods = []
        self.markers = list(self.MARKERS)
        self.markers.reverse()
        self.colors = list(self.COLORS)
        self.colors.reverse()
        self.fig = pyplot.figure(figsize=(self.page_width / 2.54,
                                          self.page_height / 2.54),
                                 frameon=False, dpi=300, facecolor='none')

    def set_periods(self, periods):
        self.periods = periods

        if periods[0].year == periods[-1].year:
            year_string = '%d' % periods[0].year
        else:
            year_string = '%d / %d' % (periods[-1].year, periods[0].year)
        pyplot.xlabel('Week (%s)' % year_string,
                      fontsize=self.axis_label_font_size)

    def add_line(self, values, label):
        if set(values) == set([None]):
            values = map(lambda x: 0 if x == None else x, values)
        else:
            values = map(lambda x: NaN if x == None else x, values)
        pyplot.plot_date(self.periods, values, '-%s' % self.markers.pop(),
                         label=label, color=self.colors.pop(),
                         linewidth=self.line_width,
                         markersize=self.marker_size)

    def get_plot(self):
        pyplot.ylabel('Patients', fontsize=self.axis_label_font_size)

        pyplot.legend(loc='upper left',
                      prop=FontProperties(size=self.legend_font_size))

        # set grid lines
        pyplot.grid(b=self.grid)

        # Set the padding between the max and min x and y values and the axis
        pyplot.axis('tight')
        xmin, xmax, ymin, ymax = pyplot.axis()
        ypad = (ymax - ymin) * (self.ypad_percentage / 100.0)
        xpad = (xmax - xmin) * (self.xpad_percentage / 100.0)
        pyplot.axis([xmin - xpad, xmax + xpad, ymin - ypad, ymax + ypad])

        # set the margins
        self.fig_left += float(self.yaxis_label_width)
        self.fig_width -= float(self.yaxis_label_width)
        self.fig_height -= float(self.xaxis_label_height)
        left = (self.fig_left / 2.54) / (self.page_width / 2.54)
        right = (self.fig_left / 2.54 + self.fig_width / 2.54) / \
                (self.page_width / 2.54)
        top = 1.0 - (self.fig_top / 2.54) / (self.page_height / 2.54)
        bottom = 1.0 - (self.fig_top / 2.54 + self.fig_height / 2.54) / \
                       (self.page_height / 2.54)
        pyplot.subplots_adjust(left=left, right=right, top=top, bottom=bottom)

        # add a title to the top
        center = (right + left) / 2.0
        top = top + (.8 / self.page_height) / 2.54
        self.fig.suptitle(self.figure_title, fontsize=10, x=center, y=top)

        # set tick font size
        ax = pyplot.gca()
        for tick in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tick.label1.set_fontsize(self.tick_font_size)

        # date format x axis ticks as week number
        ax.xaxis.set_major_formatter(mpl_dates.DateFormatter('%W'))

        chart_buffer = StringIO()
        self.fig.savefig(chart_buffer, format='pdf')

        # VERY IMPORTANT: pyplot keeps references to all figures so python
        #   won't free up the memory unless you explicitly close it
        pyplot.close(self.fig)

        return chart_buffer


def create_pdf_table(health_unit, period):
    HU_COL_WIDTH = 4 * cm
    HU_NAME_FONT_SIZE = 9
    HU_NAME_FONT = 'Helvetica'
    PAGE_HEIGHT = 21.0 * cm
    PAGE_WIDTH = 29.7 * cm

    pdf_buffer = StringIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    hu = health_unit
    hsd_clinics = HealthUnit.list_by_location(hu.hsd)

    clinic_rows = []
    for clinic in hsd_clinics:
        row = []

        # remove characters from the name if it's too long
        name = unicode(clinic)
        while c.stringWidth(name, HU_NAME_FONT, HU_NAME_FONT_SIZE) > \
                            HU_COL_WIDTH:
            name = name[:-1]

        # if it's the report for this clinic, ** the name
        # so we can find it after sort
        if clinic == hu:
            name = '**%s' % name

        row.append(name)

        complete = EpidemiologicalReport.STATUS_COMPLETED
        reps = EpidemiologicalReport.objects.filter(_status=complete)
        reps = reps.filter(clinic=clinic, period=period)

        if reps.count() == 0:
            for i in range(0, 10):
                row.append('* ')
        else:
            rep = reps[0]
            values = [rep.malaria_cases.opd_attendance,
                      rep.diseases.diseases.get(disease__code='ma').cases,
                      rep.act_consumption.yellow_dispensed,
                      rep.act_consumption.yellow_balance,
                      rep.act_consumption.blue_dispensed,
                      rep.act_consumption.blue_balance,
                      rep.act_consumption.brown_dispensed,
                      rep.act_consumption.brown_balance,
                      rep.act_consumption.green_dispensed,
                      rep.act_consumption.green_balance]

            for value in values:
                if value >= 0 and value < 9:
                    row.append('%02d' % value)
                else:
                    row.append(value)

        clinic_rows.append(row)

    # sort the datarows by OPD
    clinic_rows.sort(key=operator.itemgetter(1))

    # Now find the original health unit so it can be highlighted
    highlight_data_row = 0
    for clinic in clinic_rows:
        if clinic[0][:2] == '**':
            clinic[0] = clinic[0][2:]
            break
        highlight_data_row += 1

    hsd_type = LocationType.objects.get(name='Health Sub District')
    health_sub_districts = filter(lambda loc: loc.type == hsd_type,
                                  hu.district.descendants())

    hsd_rows = []
    for hsd in health_sub_districts:
        row = []

        row.append(unicode(hsd))

        act_report = ACTConsumptionReport.aggregate_report(hsd, [period])
        values = [MalariaCasesReport.aggregate_report(hsd, [period])['opd'],
                  DiseasesReport.aggregate_report(hsd, [period])['ma_cases'],
                  act_report['yellow_dispensed'],
                  act_report['yellow_balance'],
                  act_report['blue_dispensed'],
                  act_report['blue_balance'],
                  act_report['brown_dispensed'],
                  act_report['brown_balance'],
                  act_report['green_dispensed'],
                  act_report['green_balance']]
        for value in values:
            if value >= 0 and value < 9:
                row.append('%02d' % value)
            else:
                row.append(value)
        hsd_rows.append(row)

    district_row = []
    district_row.append(unicode(hu.district))
    act_report = ACTConsumptionReport.aggregate_report(hu.district, [period])

    opd = MalariaCasesReport.aggregate_report(hu.district, [period])['opd']
    ma = DiseasesReport.aggregate_report(hu.district, [period])['ma_cases']

    values = [opd, ma, act_report['yellow_dispensed'],
              act_report['yellow_balance'],
              act_report['blue_dispensed'],
              act_report['blue_balance'],
              act_report['brown_dispensed'],
              act_report['brown_balance'],
              act_report['green_dispensed'],
              act_report['green_balance']]

    for value in values:
        if value >= 0 and value < 9:
            district_row.append('%02d' % value)
        else:
            district_row.append(value)

    header_rows = [['Location', 'OPD', 'Malaria', 'Yellow ACT', '',
                    'Blue ACT', '', 'Brown ACT', '', 'Green ACT', ''],
                   ['', '', '', 'Disp.', 'Stock', 'Disp.', 'Stock.',
                    'Disp.', 'Stock', 'Disp.', 'Stock']]

    table_data = []
    for row in header_rows + clinic_rows + hsd_rows:
        table_data.append(row)
    table_data.append(district_row)

    col_widths = []
    col_widths.append(HU_COL_WIDTH)
    data_columns = 10
    for i in range(0, data_columns):
        col_widths.append(1 * cm)

    row_heights = []
    for i in range(0, len(table_data)):
        row_heights.append(.45 * cm)

    # My table style
    ts = [('SPAN', (0, 0), (0, 1)),
          ('SPAN', (1, 0), (1, 1)),
          ('SPAN', (2, 0), (2, 1)),
          ('SPAN', (3, 0), (4, 0)),
          ('SPAN', (5, 0), (6, 0)),
          ('SPAN', (7, 0), (8, 0)),
          ('SPAN', (9, 0), (10, 0)),

          # Outer box
          ('BOX', (0, 0), (-1, -1), 1.8, colors.black),

          # Header box
          ('BOX', (0, 0), (-1, 1), 1.8, colors.black),

          # Alternating dark horizontal lines for Disp. / Stock
          ('LINEAFTER', (0, 0), (2, -1), 1, colors.black),
          ('LINEBELOW', (3, 0), (11, 0), .25, colors.black),
          ('LINEBEFORE', (4, 0), (4, -1), .25, colors.black),
          ('LINEAFTER', (4, 0), (4, -1), 1, colors.black),
          ('LINEBEFORE', (6, 0), (6, -1), .25, colors.black),
          ('LINEAFTER', (6, 0), (6, -1), 1, colors.black),
          ('LINEBEFORE', (8, 0), (8, -1), .25, colors.black),
          ('LINEAFTER', (8, 0), (8, -1), 1, colors.black),
          ('LINEBEFORE', (10, 0), (10, -1), .25, colors.black),
          ('LINEAFTER', (10, 0), (10, -1), 1, colors.black),

          # Headers
          ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
          ('FONT', (0, 0), (-1, 1), 'Helvetica'),

          # Malaria Header
          ('FONTSIZE', (2, 0), (2, 0), 8),

          # Disp. Stock row
          ('FONTSIZE', (3, 1), (-1, 1), 8),

          # Health Unit Name
          ('FONTSIZE', (0, 2), (0, -1), HU_NAME_FONT_SIZE),
          ('FONT', (0, 2), (0, -1), 'Helvetica'),
          ('LEFTPADDING', (0, 2), (0, -1), 1.2),

          # Number cells
          ('ALIGN', (1, 2), (-1, -1), 'RIGHT'),
          ('FONT', (1, 2), (-1, -1), 'Courier'),
          ('RIGHTPADDING', (1, 2), (-1, -1), 1.5),
          ('FONTSIZE', (1, 2), (-1, -1), 9),

          # Everything
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

          # Separator line for HSD
          ('LINEABOVE', (0, len(header_rows) + len(clinic_rows)),
           (-1, len(header_rows) + len(clinic_rows)), 1.5, colors.black),

          # Separator line for District
          ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.black),
    ]

    # Zebra stripes
    start_row = len(header_rows) + 1
    for i in range(0, (len(clinic_rows) + len(hsd_rows)) / 2):
        ts.append(('BACKGROUND', (0, start_row + i * 2),
                  (-1, start_row + i * 2), colors.HexColor('#eaeaea')))

    # highlight the selected health unit
    highlight_row = len(header_rows) + highlight_data_row
    ts.append(('BOX', (0, highlight_row), (-1, highlight_row), 1, colors.red))

    styles = getSampleStyleSheet()
    ps = styles['Normal']
    ps.fontName = 'Helvetica'
    ps.alignment = 1

    elements = []
    p = Paragraph('Reporting Period:  %s to %s' %
                  (period.start_date.strftime("%a %d/%m/%Y"),
                   period.end_date.strftime("%a %d/%m/%Y")), ps)
    elements.append(p)

    table = Table(table_data, colWidths=col_widths,
                  rowHeights=row_heights, style=ts)
    elements.append(table)

    f = Frame(14.2 * cm, 1.5 * cm, 14 * cm, 18 * cm, showBoundary=0,
              topPadding=0, bottomPadding=0, rightPadding=0, leftPadding=0)
    f.addFromList(elements, c)

    # add the health unit name title to the upper left
    elements = []
    tframe = Frame(1.5 * cm, PAGE_HEIGHT-1.5 * cm - 2 * cm, 14 * cm, 2 * cm,
                   showBoundary=0, topPadding=0, bottomPadding=0,
                   rightPadding=0, leftPadding=0)

    ps.alignment = 0
    ps.fontSize = 16
    p = Paragraph(unicode(hu), ps)
    elements.append(p)
    tframe.addFromList(elements, c)

    c.showPage()
    c.save()
    return pdf_buffer


def create_district_pdfs(*args, **kwargs):

    """
    Creates a zip for each district containing a single PDF document with
    one page for each health unit.
    """
    STATIC_REPORTS_PATH = "%s/static/reports" % \
                          os.path.dirname(os.path.abspath(__file__))

    periods = ReportPeriod.objects.all()[:52]
    dates = list(periods.values_list('start_date', flat=True))

    for district in Location.objects.filter(type__name="District"):

        pdfs = []

        district_plot = LinePlot(title='District Malaria Cases', fig_width=12,
                                 fig_height=6, fig_left=1.5, fig_top=9.5)
        district_plot.set_periods(dates)

        # add district line
        label = unicode(district)
        values = []
        for period in periods:
            values.append(DiseasesReport.aggregate_report(
                                               district, [period])['ma_cases'])
        district_plot.add_line(values, label)

        # hsd lines
        hsd_type = LocationType.objects.get(name='Health Sub District')
        health_sub_districts = filter(lambda loc: loc.type == hsd_type,
                                      district.descendants())
        for hsd in health_sub_districts:
            label = unicode(hsd)
            values = []
            for period in periods:
                values.append(DiseasesReport.aggregate_report(
                                                    hsd, [period])['ma_cases'])
            district_plot.add_line(values, label)

        district_plot_buffer = district_plot.get_plot()

        for hu in HealthUnit.list_by_location(district):
            opd = []
            malaria = []
            for period in periods:
                complete = EpidemiologicalReport.STATUS_COMPLETED
                rep = EpidemiologicalReport.objects.filter(
                                  _status=complete, clinic=hu, period=period)
                if len(rep) == 0:
                    opd.append(None)
                    malaria.append(None)
                else:
                    rep = rep[0]
                    opd.append(rep.malaria_cases.opd_attendance)
                    malaria.append(rep.diseases.diseases.get(
                                                    disease__code='ma').cases)

            clinic_plot = LinePlot(title=unicode(hu), fig_width=12,
                                   fig_height=6, fig_left=1.5, fig_top=2.5)
            clinic_plot.set_periods(dates)
            clinic_plot.add_line(opd, "OPD")
            clinic_plot.add_line(malaria, "Malaria")
            clinic_plot_buffer = clinic_plot.get_plot()

            table_buffer = create_pdf_table(hu, ReportPeriod.objects.all()[1])

            district_copy = StringIO()
            district_copy.write(district_plot_buffer.getvalue())
            pdf_buffer = merge_pdfs(clinic_plot_buffer,
                                    district_copy, table_buffer)
            clinic_plot_buffer.close()

            table_buffer.close()

            temp_file = NamedTemporaryFile()
            temp_file.write(pdf_buffer.getvalue())
            temp_file.flush()
            pdfs.append(temp_file)
            pdf_buffer.close()

        district_plot_buffer.close()

        file_list = " ".join([pdf.name for pdf in pdfs])
        command = '/usr/bin/pdftk %s output \'%s/%s.pdf\'' % \
                  (file_list, STATIC_REPORTS_PATH, district.name)
        proc = Popen(command, shell=True)
        proc.wait()

        for pdf in pdfs:
            pdf.close()
