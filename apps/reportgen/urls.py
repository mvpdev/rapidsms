#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
import webapp

import reportgen.views

urlpatterns = patterns('',
    url(r'^reportgen/$', reportgen.views.ondemand, name='reportgen'),
    (r'^reportgen/ajax_progress/$', reportgen.views.ajax_progress),
    (r'^reportgen/delete/(?P<pk>\d+)$', reportgen.views.delete),
    url(r'^static/reportgen/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '%s/static/' % os.path.dirname(__file__),
                'show_indexes': False}),
)
