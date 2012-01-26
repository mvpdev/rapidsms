#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

import os

from django.conf.urls.defaults import *

import dataentry.views as views

urlpatterns = patterns('',
    url(r'^dataentry$', views.index),
    url(r'^dataentry/proxypost/?$', views.post_proxy),
)
