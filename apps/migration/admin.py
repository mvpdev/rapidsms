#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.contrib import admin

from models import ReportMalaria
from models import MigrateIDs
from models import MigrateCHW


class ReportMalariaAdmin(admin.ModelAdmin):
    list_display = ('case', 'result', \
                    'bednet', 'entered_at', 'reporter')
    verbose_name = 'Malaria Report'
    verbose_name_plural = 'Malaria Reports'

admin.site.register(ReportMalaria, ReportMalariaAdmin)
admin.site.register(MigrateIDs)
admin.site.register(MigrateCHW)
