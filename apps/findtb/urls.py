# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from findtb import views
from django.conf import settings
from django.views.generic.simple import redirect_to

urlpatterns = patterns('',

    # HOME
    url(r'findtb/$', redirect_to,
       {'url': '/findtb/eqa/'}, name='findtb-home'),

    # SEARCH
    url(r'^findtb/search/$', views.search,
        name='findtb-search',
        kwargs={'view_name': 'findtb-search'}),

    # EQA
    url(r'findtb/eqa/tracking/(?P<id>\d+)/$', views.eqa_tracking,
        name='findtb-eqa-tracking',
        kwargs={'view_name': 'findtb-eqa-tracking'}),

    url(r'^findtb/eqa/dashboard/$', views.eqa_bashboard,
        name='findtb-eqa-dashboard',
        kwargs={'view_name': 'findtb-eqa-dashboard'}),

    url(r'findtb/eqa/$', redirect_to, {'url': '/findtb/eqa/dashboard/'}),


    # SREF
    url(r'findtb/sreferral/tracking/(?P<id>\d+)/$', views.sref_tracking,
        name='findtb-sref-tracking',
        kwargs={'view_name': 'findtb-sref-tracking'}),

    url(r'^findtb/sreferral/dashboard/(?:(?P<event_type>all|alert)/)*$',
        views.sref_bashboard,
        name='findtb-sref-dashboard',
        kwargs={'view_name': 'findtb-sref-dashboard'}),

    url(r'^findtb/sreferral/$', redirect_to,
        {'url': '/findtb/sreferral/dashboard/'}),

)


if settings.DEBUG:
    urlpatterns += patterns('',

        url(r'^static/findtb/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/findtb/static', 'show_indexes': True}),

    )
