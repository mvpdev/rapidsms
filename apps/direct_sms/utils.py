#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helpers to send sms without caring about AJAX
"""

try:
    import cPickle as pickle
except ImportError:
    import pickle

import urllib2
from urllib import urlencode

from django.conf import settings


def store_log(outgoing_message, model, field='message', 
              reload_model=False, save=True):
    """
        Store the message reference into into of field of the given model.
        
        Default field is 'message'. If reload_model is True, reload a fresh
        model from the DB before processing. If save is True (default),
        the model will be saved.
    """
    if reload_model:
        model = model.__class__.objects.get(pk=r.pk)

    model.__dict__[field] = outgoing_message

    if save:
        model.save()
    
    

def send_msg(reporter, text, 
            callback=None, callback_kwargs=None, 
            log_in_model=None):
    '''
    Sends a message to a reporter using the ajax app. This goes to
    ajax_POST_send_message in the app.py.

    If you set a call back, it will be called at the message sending with
    the message as first argument, and callback_args as misc kwargs.

    Default is to use "store_log" if a model is passed.
    
    The callback function is pickled, and therfore can not be a lambda and 
    must be defined at the module level.
    It must accept **kwargs.
    '''

    if log_in_model:
        callback = store_log
        callback_kwargs = {'model': log_in_model}

    conf = settings.RAPIDSMS_APPS['ajax']
    url = "http://%s:%s/direct-sms/send_message" % (conf["host"], conf["port"])

    data = {'reporter': reporter.pk, 
           'text': text,
           'callback': pickle.dumps(callback),
           'callback_kwargs': pickle.dumps(callback_kwargs)}
           
    req = urllib2.Request(url, urlencode(data))
    stream = urllib2.urlopen(req)
    stream.close()


