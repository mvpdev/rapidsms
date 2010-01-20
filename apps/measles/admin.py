#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin

from models import ReportMeasles


class ReportMeaslesAdmin(admin.ModelAdmin):
    list_display = ('case', 'reporter', 'taken', 'entered_at', 'location')
    list_filter = ('taken',)
    search_fields = ['location__name', ]

admin.site.register(ReportMeasles, ReportMeaslesAdmin)
