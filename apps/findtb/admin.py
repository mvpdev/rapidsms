#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.contrib import admin

from findtb.models import *
from django_tracking.models import *


admin.site.register(Configuration)
admin.site.register(Role)
admin.site.register(Specimen)
admin.site.register(Patient)
admin.site.register(State)
admin.site.register(TrackedItem)
admin.site.register(SlidesBatch)
admin.site.register(Slide)
