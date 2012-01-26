#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

from django.contrib import admin
from models import *
from django.utils.translation import ugettext_lazy as _

admin.site.register(Configuration)

admin.site.register(ReportPeriod)
admin.site.register(Disease)
admin.site.register(DiseaseObservation)
admin.site.register(DiseasesReport)
admin.site.register(EpidemiologicalReport)
admin.site.register(MalariaCasesReport)
admin.site.register(MalariaTreatmentsReport)
admin.site.register(ACTConsumptionReport)

admin.site.register(DiseaseAlertTrigger)
admin.site.register(DiseaseAlert)

admin.site.register(WebUser)
admin.site.register(HealthUnit)
