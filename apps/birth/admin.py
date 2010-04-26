#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin
from birth.models import ReportBirth


class ReportBirthAdmin(admin.ModelAdmin):
    list_display = ('case', 'display_name', 'display_dob', 'weight', \
                    'entered_at', 'complications')
    search_fields = ['case__first_name', 'case__last_name']
    list_filter = ('weight',)
    ordering = ('-entered_at',)
admin.site.register(ReportBirth, ReportBirthAdmin)
