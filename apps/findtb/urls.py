# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from findtb import views
from django.conf import settings



urlpatterns = patterns('',

    url(r'tracking/(?P<id>\d+)/$', views.tracking, name="findtb-tracking"),
    url(r'^tracking/$', views.home, name="findtb-tracking-home"),
    

)


if settings.DEBUG:
    urlpatterns += patterns('',

        url(r'^static/findtb/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/findtb/static', 'show_indexes': True}),

    )
