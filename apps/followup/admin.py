#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin

from followup.models import ReportImmunization


class ReportVaccineAdmin(admin.ModelAdmin):
    list_display = ('case', 'reporter', 'vaccine', 'period', 'entered_at')
    list_filter = ('vaccine', )
    search_fields = ['case__ref_id', ]

admin.site.register(ReportImmunization, ReportVaccineAdmin)
