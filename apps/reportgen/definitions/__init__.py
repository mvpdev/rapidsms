#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

__all__ = ('MvisIndicators', 'MvisIndicatorsTwo','ChwList','Utilization',\
    'PatientList', 'Malnutrition', 'MedicineGivenReport', \
    'StatsDataEntry', 'Operational', 'StatsOmrs', 'PregnancyReport', \
    'ChwReport', 'ChwManagerReport', 'PerformanceCharts', 'UnderFive', \
    'IndicatorChart', 'ChwLog', 'PMTCTDefaulters', 'SpotCheck', \
    'VitalEventsReport', 'IdentityCards', 'SmsUsage', 'PList', \
    'ChwHouseholdVisitCoverage', 'LabReport', 'NotAttendingSchoolReport', \
    'PregnantWomenEDDsixweeks')

# This is the way we get the celery workers
# to register all of the ReportDefinition tasks
from reportgen.definitions import *

