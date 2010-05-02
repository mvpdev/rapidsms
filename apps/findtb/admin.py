#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.contrib import admin

from findtb.models import *


admin.site.register(Configuration)
admin.site.register(Role)
admin.site.register(Specimen)
admin.site.register(Patient)

