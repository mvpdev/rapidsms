#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helpers to send sms without caring about AJAX
"""

import urllib2
from urllib import urlencode

from django.conf import settings

def send_msg(reporter, text):
   '''
    Sends a message to a reporter using the ajax app. This goes to
    ajax_POST_send_message in the app.py
    '''

   conf = settings.RAPIDSMS_APPS['ajax']
   url = "http://%s:%s/direct-sms/send_message" % (conf["host"], conf["port"])

   data = {'reporter': reporter.pk, \
           'text': text}
   req = urllib2.Request(url, urlencode(data))
   stream = urllib2.urlopen(req)
   stream.close()


