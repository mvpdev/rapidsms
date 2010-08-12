#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Let your send message using Ajax.
"""

import rapidsms
from reporters.models import Reporter

try:
    import cPickle as pickle
except ImportError:
    import pickle
    
def return_none(**kwargs): pass

from exceptions import DirectSmsError

PICKLED_LAMBDA = pickle.dumps( return_none)
PICKLED_DICT = pickle.dumps({})


class App (rapidsms.app.App):
    """
    Helper to send a message trough Ajax
    """

    def handle(self, message):
        pass


    def ajax_POST_send_message(self, urlparser, post):
        """
        Callback method for sending messages from the webui via the ajax app.

        You can pass it a serialized callbacks with args, and either choose
        to send a message to a given reporter or to an anonymous one,
        according to a backend and an indentity.         
        """
        
        callback = pickle.loads(post.get('callback', 
                                            PICKLED_LAMBDA)) or return_none
        callback_kwargs = pickle.loads(post.get('callback_kwargs', 
                                        PICKLED_DICT)) or {}
        
        backend_slug = post.get('backend', '')
        identity = post.get('identity', '')
        
        if not backend_slug or not identity:
            try:
                rep = Reporter.objects.get(pk=post.get('reporter', -1))
            except Reporter.DoesNotExist:
                raise DirectSmsError(u"You need to specify either a valid "\
                                     u"reporter or a valid backend & identity")
            else:
                pconn = rep.connection()

                # abort if we don't know where to send the message to
                # (if the device the reporter registed with has been
                # taken by someone else, or was created in the WebUI)
                if not pconn:
                   raise DirectSmsError("%s is unreachable (no connection)" % rep)
                   
                backend_slug = pconn.backend.slug
                identity = pconn.identity

        # attempt to send the message
        be = self.router.get_backend(backend_slug)
        
        if not be:
            raise DirectSmsError(u"The backend '%s' is not installed. "\
                                 u"Check your 'local.ini' file." \
                                 % backend_slug )
        
        message = be.message(identity, post["text"])
        
        callback(outgoing_message=message, **callback_kwargs)
        
        sent = message.send()

        # attempt to call the callback 
        
        return sent
        
