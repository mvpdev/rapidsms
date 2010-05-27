#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin

import childcount.views as views
import childcount.reports as reports

admin.autodiscover()

# an issue between Django version 1.0 and later?
# see http://code.djangoproject.com/ticket/10050
try:
    admin_urls = (r'^admin/', include(admin.site.urls))
except AttributeError:
    # Django 1.0 admin site
    admin_urls = (r'^admin/(.*)', admin.site.root)

urlpatterns = patterns('',
    admin_urls,
    url(r'^childcount/?$', views.index),
    url(r'^childcount/patients/?$', views.patient),
    url(r'^childcount/patients/(?P<rfilter>[a-z]+)/(?P<rformat>[a-z]+)?$', \
        reports.all_patient_list_pdf),
    url(r'^childcount/patients_per_chw/pdf/?$', \
                                    reports.all_patient_list_per_chw_pdf),
    url(r'^childcount/chw/?$', views.chw),
    url(r'^childcount/chws/(?P<rformat>[a-z]*)$', reports.chw),
    url(r'^childcount/nutrition.png', views.nutrition_png),
    url(r'^childcount/sms.png', views.sms_png),
    url(r'^childcount/under_five', reports.under_five),

    url(r'^childcount/dataentry/?$', views.dataentry),
)
