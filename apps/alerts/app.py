#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rapidsms
from reporters.models import Reporter
from logger_ng.models import LoggedMessage
from alerts.models import SmsAlertModel

class App (rapidsms.app.App):
    """
    Helper to send a message trough Ajax
    """

    def handle(self, message):
        return False


    def ajax_POST_send_message(self, urlparser, post):
       """
       Callback method for sending messages from the webui via the ajax app.
       """
       rep = Reporter.objects.get(pk=post["reporter"])
       alert = SmsAlertModel.objects.get(pk=post["alert_id"])
       pconn = rep.connection()

       # abort if we don't know where to send the message to
       # (if the device the reporter registed with has been
       # taken by someone else, or was created in the WebUI)
       if pconn is None:
           raise Exception("%s is unreachable (no connection)" % rep)

       # attempt to send the message
       # TODO: what could go wrong here?
       be = self.router.get_backend(pconn.backend.slug)
       if be is None:
           raise Exception("No backend for %s" % pconn.backend.slug)

       outgoing_message = be.message(pconn.identity, post["text"])
       sent = outgoing_message.send()
       message = LoggedMessage.objects.get(pk=outgoing_message.logger_id)
       message.status = LoggedMessage.STATUS_INFO
       message.save()
       alert.outgoing_message = message
       alert.save()
       
       return sent 
