#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rapidsms
from reporters.models import Reporter
from logger.models import OutgoingMessage
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
       outgoing_message = be.message(pconn.identity, post["text"])
       sent = outgoing_message.send()
       message = OutgoingMessage.objects.get(pk=outgoing_message.logger_id)
       alert.outgoing_message = message
       alert.save()
       
       return sent 
