#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
logger_ng app urls
'''

from django.conf.urls.defaults import *
import logger_ng.views as views

urlpatterns = patterns('',
    url(r'^logger_ng/?$', views.index),
)
