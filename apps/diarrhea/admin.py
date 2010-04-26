#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.contrib import admin

from models import ReportDiarrhea, DiarrheaObservation


class ReportDiarrheaAdmin(admin.ModelAdmin):
    list_display = ("case", "ors", "days", "entered_at", "status")

admin.site.register(ReportDiarrhea, ReportDiarrheaAdmin)

admin.site.register(DiarrheaObservation)
