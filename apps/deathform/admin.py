#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin
from deathform.models.general import ReportDeath


class ReportDeathAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'gender', 'cause', 'where', \
                    'dod', 'entered_at', 'description')
    search_fields = ['first_name', 'last_name']
    list_filter = ('dod',)
    ordering = ('-dod',)
admin.site.register(ReportDeath, ReportDeathAdmin)
