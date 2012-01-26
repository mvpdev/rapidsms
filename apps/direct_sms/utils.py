#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

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

from exceptions import DirectSmsError

LOGGER_CLS =  None

# try to store log using the usual logger
try:
    from logger.models import OutgoingMessage as LOGGER_CLS
except ImportError:
    pass
    
# try to store log using the new logger  
try:
    from logger_ng.models import LoggedMessage as LOGGER_CLS
except ImportError:
    pass
        
def store_log(outgoing_message, model, field='message', 
                  reload_model=False, save=True):
        """
            Store the message reference into into a field of the given model.
            
            It's a convenience function for something we do often.
            
            Default field is 'message'. If reload_model is True, reload a fresh
            model from the DB before processing. If save is True (default),
            the model will be saved.
        """
        outoing_message = LOGGER_CLS.objects.get(pk=outgoing_message.logger_id)
        
        if reload_model:
            model = model.__class__.objects.get(pk=r.pk)

        model.__dict__[field] = outgoing_message

        if save:
            model.save()
            
            
# no logger present, this shorcut can't work
if not LOGGER_CLS:

    def store_log(outgoing_message, model, field='message', 
                  reload_model=False, save=True):
        """
            Prevent this fonction to be used.
        """
        raise DirectSmsError(u"No compatible logger application is present")



def send_msg(reporter=None, text='', 
            callback=None, callback_kwargs=None, 
            post_send_callback=None, post_send_callback_kwargs=None,
            log_in_model=None, backend='', identity=''):
    '''
    Sends a message to a reporter using the ajax app. This goes to
    ajax_POST_send_message in the app.py.

    If you set a call back, it will be called before the message sending with
    the message as first argument, and callback_args as misc kwargs.
    
    If you wish to execute something AFTER the message has been sent, go for
    post_send_callback instead.

    Default is to use "store_log" if a model is passed.
    
    The callback function is pickled, and therfore can not be a lambda and 
    must be defined at the module level.
    It must accept **kwargs.
    '''

    if log_in_model:
        post_send_callback = store_log
        post_send_callback_kwargs = {'model': log_in_model}

    conf = settings.RAPIDSMS_APPS['ajax']
    url = "http://%s:%s/direct-sms/send_message" % (conf["host"], conf["port"])
    
    data = {'text': text,
            'pre_send_callback': pickle.dumps(callback),
            'pre_send_callback_kwargs': pickle.dumps(callback_kwargs),
            'post_send_callback': pickle.dumps(post_send_callback),
            'post_send_callback_kwargs': pickle.dumps(post_send_callback_kwargs)}

    try:
        data['reporter'] = reporter.pk
    except AttributeError:
        pass
        
    data['backend'] = backend
    data['identity'] = identity
           
    req = urllib2.Request(url, urlencode(data))
    stream = urllib2.urlopen(req)
    stream.close()



