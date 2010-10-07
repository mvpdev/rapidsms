# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from findtb import views
from django.conf import settings
from django.views.generic.simple import redirect_to

urlpatterns = patterns('',

    # HOME
    url(r'findtb/$', views.index, name='findtb-home'),

    # SEARCH
    url(r'^findtb/search/$', views.FindtbSearchView(),
        name='findtb-search'),

    # DOC
    url(r'^findtb/doc/$', views.global_views.doc,
        name='findtb-doc'),

    # NOTICE
    url(r'^findtb/notices/$', views.notices,
        name='findtb-notices',
        kwargs={'view_name': 'findtb-notices'}),

    # REPORTS
    url(r'^findtb/reports/$', views.reports,
        name='findtb-reports',
        kwargs={'view_name': 'findtb-reports'}),


)


# EQA (tracking)
urlpatterns += patterns('',

    url(r'^findtb/eqa/tracking/(?P<id>\d+)/(?:(?P<year>\d{4})/(?P<quarter>[1-4])/)(?:(?P<dtu>[a-z0-9\-]+)/)?collected-from-first-controller/$',
        views.collected_from_first_controller,
        name='findtb-eqa-collected_from_first_controller',
        kwargs={'view_name': 'findtb-eqa-collected_from_first_controller'}),

    url(r'^findtb/eqa/tracking/(?P<id>\d+)/(?:(?P<year>\d{4})/(?P<quarter>[1-4])/)(?:(?P<dtu>[a-z0-9\-]+)/)?delivered-to-second-controller/$',
        views.delivered_to_second_controller,
        name='findtb-eqa-delivered_to_second_controller',
        kwargs={'view_name': 'findtb-eqa-delivered_to_second_controller'}),
        
    url(r'^findtb/eqa/tracking/(?P<id>\d+)/(?:(?P<year>\d{4})/(?P<quarter>[1-4])/)(?:(?P<dtu>[a-z0-9\-]+)/)?results-available/$',
        views.results_available,
        name='findtb-eqa-results_available',
        kwargs={'view_name': 'findtb-eqa-results_available'}),
)

# EQA (general)
urlpatterns += patterns('',

    url(r'^findtb/eqa/tracking/(?P<id>\d+)/(?:(?P<year>\d{4})/(?P<quarter>[1-4])/(?:(?P<dtu>[a-z0-9\-]+)/)?)?$',
        views.eqa_views.eqa_tracking,
        name='findtb-eqa-tracking',
        kwargs={'view_name': 'findtb-eqa-tracking'}),

    url(r'^findtb/eqa/dashboard/(?:(?P<event_type>all|alert)/)*$', views.eqa_dashboard,
        name='findtb-eqa-dashboard',
        kwargs={'view_name': 'findtb-eqa-dashboard'}),

    url(r'^findtb/eqa/$', redirect_to, {'url': '/findtb/eqa/dashboard/'}),
    
    url(r'^findtb/eqa/controllers$', views.controllers,
        name='findtb-eqa-controllers',
        kwargs={'view_name': 'findtb-eqa-controllers'}),
        
    url(r'^findtb/eqa/progress/$', views.progress,
        name='findtb-eqa-progress',
        kwargs={'view_name': 'findtb-eqa-progress'}),

)


# SREF (tracking)
urlpatterns += patterns('',

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/incoming/$',
        views.sref_incoming,
        name='findtb-sref-registered',
        kwargs={'view_name': 'findtb-sref-registered'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/incoming/$',
        views.sref_incoming,
        name='findtb-sref-sent',
        kwargs={'view_name': 'findtb-sref-sent'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/invalid/$',
        views.sref_invalid,
        name='findtb-sref-invalid',
        kwargs={'view_name': 'findtb-sref-invalid'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/done/$',
        views.sref_done,
        name='findtb-sref-done',
        kwargs={'view_name': 'findtb-sref-done'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/received/$',
        views.sref_received,
        name='findtb-sref-received',
        kwargs={'view_name': 'findtb-sref-received'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/invalidate/$',
        views.sref_invalidate,
        name='findtb-sref-invalidate',
        kwargs={'view_name': 'findtb-sref-invalidate'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/microscopy/$',
        views.sref_microscopy,
        name='findtb-sref-microscopy',
        kwargs={'view_name': 'findtb-sref-microscopy'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/lpa/$',
        views.sref_lpa,
        name='findtb-sref-lpa',
        kwargs={'view_name': 'findtb-sref-lpa'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/lj/$',
        views.sref_lj,
        name='findtb-sref-lj',
        kwargs={'view_name': 'findtb-sref-lj'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/mgit/$',
        views.sref_mgit ,
        name='findtb-sref-mgit',
        kwargs={'view_name': 'findtb-sref-mgit'}),

)


# SREF (general)
urlpatterns += patterns('',


    url(r'^findtb/sreferral/$', redirect_to,
        {'url': '/findtb/sreferral/dashboard/'}),

    url(r'^findtb/sreferral/dashboard/(?:(?P<event_type>all|alert)/)*$',
        views.sref_dashboard,
        name='findtb-sref-dashboard',
        kwargs={'view_name': 'findtb-sref-dashboard'}),

    url(r'findtb/sreferral/tracking/(?P<id>\d+)/$', views.sref_tracking,
        name='findtb-sref-tracking',
        kwargs={'view_name': 'findtb-sref-tracking'}),

    # when something doesn't exist, redirect to dashboard
    url(r'^findtb/sreferral/\S*$', redirect_to,
        {'url': '/findtb/sreferral/dashboard/'}),

)


if settings.DEBUG:
    urlpatterns += patterns('',

        url(r'^static/findtb/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/findtb/static', 'show_indexes': True}),

    )
    
    
