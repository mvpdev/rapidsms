#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' dataentry backend client

WIP: Do not use as this will be broken very soon '''

import datetime
import urllib
import urllib2
import random

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from rapidsms.webui.utils import render_to_response
from rapidsms.webui import settings


def index(req):
    ''' displays basic U.I '''
    return render_to_response(req, 'dataentry/index.html', {})


def post_proxy(request):
    ''' HTTP proxy to forward AJAX calls to dataentry backend '''

    if not request.method == 'POST':
        return HttpResponse(u"POST?")

    conf = settings.RAPIDSMS_APPS['dataentry']
    url = "http://%s:%s" % (conf["host"], conf["port"])

    data = request.POST.urlencode()
    print data
    req = urllib2.Request(url, data)
    stream = urllib2.urlopen(req)

    return HttpResponse(stream.read(), mimetype="application/json")
    

def post_commcare(request):
    ''' HTTP proxy to forward AJAX calls to dataentry backend '''

    if not request.method == 'POST':
        return HttpResponse(u"POST?")

    conf = {}

    try:
        conf = settings.RAPIDSMS_CONF['commcare']
    except:
        conf['port']  = 1339
        conf['host'] = 'localhost'

    url = "http://%s:%s" % (conf["host"], conf["port"])

    data = request.POST.urlencode()
    print data
    req = urllib2.Request(url, data)
    stream = urllib2.urlopen(req)

    return HttpResponse(stream.read(), mimetype="application/json")
