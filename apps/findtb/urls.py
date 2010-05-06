# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from findtb import views
from django.conf import settings
from django.views.generic.simple import redirect_to

urlpatterns = patterns('',

    # HOME
    url(r'findtb/$', redirect_to,
       {'url': '/findtb/sreferral/'}, name='findtb-home'),

    # SEARCH
    url(r'^findtb/search/$', views.search,
        name='findtb-search',
        kwargs={'view_name': 'findtb-search'}),
)


# EQA
urlpatterns += patterns('',
    url(r'findtb/eqa/tracking/(?P<id>\d+)/$', views.eqa_tracking,
        name='findtb-eqa-tracking',
        kwargs={'view_name': 'findtb-eqa-tracking'}),

    url(r'^findtb/eqa/dashboard/$', views.eqa_bashboard,
        name='findtb-eqa-dashboard',
        kwargs={'view_name': 'findtb-eqa-dashboard'}),

    url(r'findtb/eqa/$', redirect_to, {'url': '/findtb/eqa/dashboard/'}),

)


# SREF (general)
urlpatterns += patterns('',


    url(r'^findtb/sreferral/$', redirect_to,
        {'url': '/findtb/sreferral/dashboard/'}),

    url(r'^findtb/sreferral/dashboard/(?:(?P<event_type>all|alert)/)*$',
        views.sref_bashboard,
        name='findtb-sref-dashboard',
        kwargs={'view_name': 'findtb-sref-dashboard'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/$', views.sref_tracking,
        name='findtb-sref-tracking',
        kwargs={'view_name': 'findtb-sref-tracking'}),

)


# SREF (tracking)
urlpatterns += patterns('',

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/incoming/$',
        views.sref_incoming,
        name='findtb-sref-incoming',
        kwargs={'view_name': 'findtb-sref-incoming'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/microscopy/$',
        views.sref_microscopy,
        name='findtb-sref-microscopy',
        kwargs={'view_name': 'findtb-sref-microscopy'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/lpa/$',
        views.sref_tracking,
        name='findtb-sref-lpa',
        kwargs={'view_name': 'findtb-sref-lpa'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/mgit/$',
        views.sref_tracking,
        name='findtb-sref-mgit',
        kwargs={'view_name': 'findtb-sref-mgit'}),

)





if settings.DEBUG:
    urlpatterns += patterns('',

        url(r'^static/findtb/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/findtb/static', 'show_indexes': True}),

    )
