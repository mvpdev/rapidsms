# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from findtb import views
from django.conf import settings
from django.views.generic.simple import redirect_to



urlpatterns = patterns('',

    url(r'eqa/tracking/(?P<id>\d+)/$', views.tracking, name="findtb-eqa-tracking"),
    url(r'^eqa/dashboard/$', views.home, name="findtb-eqa-dashboard"),
    url(r'^eqa/search/(?P<searched>\w+)*$', views.home, name="findtb-eqa-search"),
    url(r'^eqa/$', redirect_to, {'url': '/eqa/dashboard/'}),
    
    url(r'sreferral/tracking/(?P<id>\d+)/$', views.tracking, name="findtb-sreferral-tracking"),
    url(r'^sreferral/dashboard/$', views.home, name="findtb-sreferral-dashboard"),
    url(r'^sreferral/search/(?P<searched>\w+)*$', views.home, name="findtb-sreferral-search"),
    url(r'^sreferral/$', redirect_to, {'url': '/sreferral/dashboard/'}),

)


if settings.DEBUG:
    urlpatterns += patterns('',

        url(r'^static/findtb/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/findtb/static', 'show_indexes': True}),

    )
