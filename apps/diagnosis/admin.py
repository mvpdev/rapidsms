#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin

from diagnosis.models import Diagnosis, DiagnosisCategory, ReportDiagnosis

admin.site.register(Diagnosis)
admin.site.register(DiagnosisCategory)


class ReportDiagnosisAdmin(admin.ModelAdmin):
    list_display = ('case', 'entered_at')

admin.site.register(ReportDiagnosis, ReportDiagnosisAdmin)
