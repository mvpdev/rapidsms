# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from findtb import views
from django.conf import settings
from django.views.generic.simple import redirect_to

urlpatterns = patterns('',

    # HOME
    url(r'findtb/$', redirect_to, 
       {'url': '/findtb/eqa/'}, name='findtb-home'),


    # EQA
    url(r'findtb/eqa/tracking/(?P<id>\d+)/$', views.tracking, 
        name='findtb-eqa-tracking', 
        kwargs={'view_name': 'findtb-eqa-tracking'}),
        
    url(r'^findtb/eqa/dashboard/$', views.home, 
        name='findtb-eqa-dashboard', 
        kwargs={'view_name': 'findtb-eqa-dashboard'}),
        
    url(r'^findtb/eqa/search/(?P<searched>\w+)*$', views.home, 
        name='findtb-eqa-search', 
        kwargs={'view_name': 'findtb-eqa-search'}),
        
    url(r'findtb/eqa/$', redirect_to, {'url': '/findtb/eqa/dashboard/'}),
    
    
    # SREF
    url(r'findtb/sreferral/tracking/(?P<id>\d+)/$', views.tracking, 
        name='findtb-sreferral-tracking', 
        kwargs={'view_name': 'findtb-sreferral-tracking'}),
        
    url(r'^findtb/sreferral/dashboard/$', views.home, 
        name='findtb-sreferral-dashboard', 
        kwargs={'view_name': 'findtb-sreferral-dashboard'}),
        
    url(r'^findtb/sreferral/search/(?P<searched>\w+)*$', views.home, 
        name='findtb-sreferral-search', 
        kwargs={'view_name': 'findtb-sreferral-search'}),
        
    url(r'^findtb/sreferral/$', redirect_to, 
        {'url': '/findtb/sreferral/dashboard/'}),

)


if settings.DEBUG:
    urlpatterns += patterns('',

        url(r'^static/findtb/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/findtb/static', 'show_indexes': True}),

    )
