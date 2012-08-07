#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: mvpdev

"""Holds view logic for the dashboard.
"""



from django.utils import simplejson
from django.utils.translation import ugettext as _

from childcount.models import Patient
from childcount.indicators import nutrition
from childcount.helpers import site

from reportgen.timeperiods import Month, FourWeeks

def registration_chart():
    """
    This method corresponds to the template 
    :file:`dashboard_sections/registration_chart.html`

    It returns only the data needed to build the chart, which is passed to a javascript
    object in a JSON string using :func:`simplejson.dumps()`.
    """
    
    days_past, num_registrations = Patient.registrations_by_date()
    
    reg_chart_data = { 'yAxis': _(u"Total Number of Patients"), \
                       'xAxis': _(u"Number of days ago"),
            'daysPast' : days_past, 'regCount': num_registrations }
    
    return simplejson.dumps(reg_chart_data)


def highlight_stats_bar():
    """
    Corresponds to template: :file:`dashboard_sections/highlight_stats_bar.html`
    
    This :func:`dict` is structured to easily pump into an HTML table.
    """
    return {'titles': [_(u"# of Households"), _(u"# of Patients"), \
                       _(u"# of Underfives"), _(u"# of Pregnant Women")], \
                        'data': [532, 1521, 534, 0] }

def nutrition_chart():
    """Data for a pie chart
    of nutrition statistics.
    """
    period = FourWeeks.periods()[3]

    unknown = nutrition.Unknown(period, Patient.objects.all())
    healthy = nutrition.Healthy(period, Patient.objects.all())
    moderate = nutrition.Mam(period, Patient.objects.all())

    nutrition_data_for_dashboard = [[_(u"Unknown"), unknown], \
                                    [_(u"Healthy"), healthy], \
                                    [_(u"Moderate"), moderate]]
    
    return simplejson.dumps(nutrition_data_for_dashboard)

def recent_numbers():
    """
    Pumps a python :func:`dict` with "columns" and "rows"(&data) which is
    then turned into a pretty HTML table
    """

    month = Month.periods()[0]
    last_month = Month.periods()[1]
    generated_report_data = {'month': site.summary_stats(month), \
                            'last_month': site.summary_stats(last_month) }
   
    recent_numbers_columns = [[_(u"This Month (to date)"), 'month'], [_(u"Last Month"), 'last_month']]
    named_rows = [[_(u"+SAM / MAM"),"num_mam_sam"], [_(u"RDT+"), 'num_rdt']]
   
    recent_numbers_data = []
    for row in named_rows:
        row_id = row[1]
        recent_numbers_data.append([row[0], [generated_report_data[dt[1]][row_id] for dt in recent_numbers_columns]])
    
    return {'columns': [c[0] for c in recent_numbers_columns], 'rows': recent_numbers_data}
    
