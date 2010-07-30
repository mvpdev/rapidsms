#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helpers to send sms without caring about AJAX
"""

import datetime
import urllib2
from urllib import urlencode

from celery.task import Task
from celery.decorators import task
from celery.registry import tasks
from djcelery.models import TaskMeta

from django.conf import settings
from django.utils.translation import ugettext as _

from models import SmsAlertModel

def send_msg(reporter, text, alert):
   '''
    Sends a message to a reporter using the ajax app. This goes to
    ajax_POST_send_message in the app.py
    '''
   conf = settings.RAPIDSMS_APPS['ajax']
   url = "http://%s:%s/alerts/send_message" % (conf["host"], conf["port"])

   data = {'reporter': reporter.pk, 
           'text': text,
           'alert_id': alert.pk}
   req = urllib2.Request(url, urlencode(data))
   stream = urllib2.urlopen(req)
   stream.close()



@task()
def delayed_sms_alert(alert_id, msg):
    alert = SmsAlertModel.objects.get(pk=alert_id)
    send_msg(alert.reporter, msg, alert)
tasks.register(delayed_sms_alert)



# callbacks, cancel and delay
class SmsAlert(object):


    def __init__(self, 
                 msg,
                 callback=lambda *x, **y : None,
                 callback_args=(),
                 callback_kwargs={},
                 abort_callback=lambda *x, **y : False,
                 abort_callback_args=(),
                 abort_callback_kwargs={},
                 *args, 
                 **kwargs):

        self.msg = msg
        
        self.callback = callback
        self.callback_args = callback_args 
        self.callback_kwargs = callback_kwargs
        
        self.abort_callback_args = abort_callback_args 
        self.abort_callback_kwargs = abort_callback_kwargs
        self.abort_callback = abort_callback

        self.data = SmsAlertModel(*args, 
                                      **kwargs)
        

    def send(self, send_at=None, delay=None):
        '''
        Send the Sms, with delay if required
        '''

        if self.data.pk:
            raise Exception("Send can't be called twice'")

        # save so the logger can pull it from the db
        self.data.save()

        if not send_at and not delay:
            send_msg(self.data.reporter, self.msg, self.data)
            self.data = SmsAlertModel.objects.get(pk=self.data.pk)
        else:
            if not send_at:
                send_at = datetime.datetime.today()

            if not delay:
                delay = datetime.timedelta(seconds=0)

            eta = send_at + delay

            result = delayed_sms_alert.apply_async(args=(self.data.pk, 
                                                         self.msg), 
                                                   eta=eta)
            self.data.task_meta = TaskMeta.objects.get_task(result.task_id)

        
        self.data.save()

        return self.data
        
