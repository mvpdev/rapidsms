#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin

from models import ReportMalnutrition


class ReportMalnutritionAdmin(admin.ModelAdmin):
    list_display = ('case', 'name', 'location', 'muac', 'entered_at', \
                    'reporter')
    search_fields = ['case__ref_id', 'reporter__first_name', \
                     'reporter__last_name']

admin.site.register(ReportMalnutrition, ReportMalnutritionAdmin)
