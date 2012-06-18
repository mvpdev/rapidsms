#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import os

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
import webapp

from childcount import views
from childcount import uploadhealthids

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

    # webapp URLS
    url(r'^accounts/login/$', "webapp.views.login",
        {'template_name': 'childcount/login.html'}, name='login'),
    url(r'^accounts/logout/$', "webapp.views.logout",
        {'template_name': 'childcount/loggedout.html'}, name='logout'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url('^static/webapp/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': '%s/static' % os.path.dirname(webapp.__file__)}),

    url(r'^$', views.index, name='dashboard'),
    url(r'^childcount/?$', views.index, name='cc-dashboard'),
    url(r'^childcount/patients/?$', views.patient, name='cc-patients'),
    url(r'^childcount/patients/edit/((?P<healthid>[a-zA-Z0-9]+)/)?$',
        views.edit_patient, name='cc-edit_patient'),
    url(r'^childcount/patients/(?P<chw>[a-zA-Z0-9]+)/?$',
        views.patient, name='cc-patients'),

    url(r'^childcount/chws.json/?$', views.chw_json),
    url(r'^childcount/add_chw/?$', views.add_chw, name='cc-add_chw'),
    url(r'^childcount/list_chw/?$', views.list_chw, name='cc-list_chw'),
    url(r'^childcount/change_chw/(?P<chw>[a-zA-Z0-9\-\_\.]*)/?$',
        views.change_chw, name='cc-change_chw'),
    url(r'^childcount/chw-connections/(?P<chw>[a-zA-Z0-9\-\_\.]*)/?$',
        views.change_chw_connections, name='cc-chw-connections'),
    url(r'^childcount/list_location/?$', views.list_location,
        name='cc-list_location'),
    url(r'^childcount/change_location/(?P<location>\d+)/?$',
        views.change_chw_by_location, name='cc-change_location'),
    url(r'^childcount/patient-by-location/(?P<location>\d+)/?$',
        views.patient_by_location, name='cc-patients-by-location'),
    url(r'^childcount/indicators/?$', views.indicators, name='cc-indicators'),

    url(r'^childcount/dataentry/?$', views.dataentry, name='cc-dataentry'),
    url(r'^childcount/dataentry/form/(?P<formid>[a-zA-Z0-9\-\_\.]*)/?$',
                        views.form, name='form'),
    url(r'^childcount/site_summary/(?P<report>[a-z_]*)/(?P<format>[a-z]*)$',
        views.site_summary),

    url(r'^childcount/upload-healthid-file',
        uploadhealthids.upload_file, name='cc-upload-hids'),

    url(r'^childcount/dashboard-section/(?P<section_name>[a-z_]*)/$',
        views.get_dashboard_section, name='cc-dashboard-section'),

    url(r'^childcount/lab/?$', views.lab, name='cc-lab'),
    
    #url(r'^childcount/upload-healthid-file', uploadhealthids.upload_file, name='cc-upload-hids'),

)
