#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

__all__ = ('MvisIndicators','ChwList','Utilization',\
    'PatientList', 'Malnutrition', 'MedicineGivenReport', \
    'StatsDataEntry', 'Operational', 'StatsOmrs', \
    'ChwReport', 'ChwManagerReport', 'PerformanceCharts',
    'IndicatorChart', 'ChwLog', 'PMTCTDefaulters', 'SpotCheck', \
    'VitalEventsReport', 'IdentityCards', 'SmsUsage')

# This is the way we get the celery workers
# to register all of the ReportDefinition tasks
from reportgen.definitions import *

