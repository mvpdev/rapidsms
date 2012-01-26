#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

from django.contrib import admin
from datetime import datetime
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from models import Configuration, MessageLog, Record


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'value')
    ordering = ('key',)


class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'date',)
    list_filter = ['date', 'sender']
    ordering = ('-id',)


class RecordAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'date', 'value', 'kind')
    list_filter = ['kind', 'date', 'sender']
    ordering = ('-date',)

admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(MessageLog, MessageLogAdmin)
admin.site.register(Record, RecordAdmin)
