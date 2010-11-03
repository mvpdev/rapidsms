#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('',
    (r'^static/cc_ui/(?P<path>.*)$', 'django.views.static.serve', \
    {'document_root': 'apps/cc_ui/static', 'show_indexes': True}),
      )
