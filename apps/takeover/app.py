#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

'''Takeover app

when using the httptester, it gives a number a http identity if the
number was of a registered reporter
'''

from functools import wraps
import re

from django.utils.translation import ugettext as _
from django.db import models

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from reporters.models import PersistantBackend, Reporter
from childcount.models.logs import MessageLog
from childcount.models.config import Configuration as Cfg


class HandlerFailed (Exception):
    pass

'''Had this for an @wraps decorator testing
def adeco(func):
    @wraps(func)
    def wrapper(self, *args):
        print("A decorator func")
        print func.__doc__
        return func(self, *args)
    return wrapper

def anotherdeco(func):
    @wraps(func)
    def wrapper(self, *args):
        print("Another decorator func")
        print func.__doc__
        return func(self, *args)
    return wrapper
'''


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"%s") % \
                "Sorry, only registered users can access this program.")
            return True
    return wrapper


class App (rapidsms.app.App):

    '''Takeover app

    when using the httptester, it gives a number a http identity if the
    number was of a registered reporter
    takeover @alias
    '''

    MAX_MSG_LEN = 140
    keyword = Keyworder()
    handled = False

    def start(self):
        '''Configure your app in the start phase.'''
        pass

    def parse(self, message):
        ''' Parse incoming messages.

        flag message as not handled '''
        message.was_handled = False

    def handle(self, message):
        ''' Function selector

        Matchs functions with keyword using Keyworder
        Replies formatting advices on error
        Return False on error and if no function matched '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            # make sure we tell them that we got a problem
            command_list = [method for method in dir(self) \
                            if hasattr(getattr(self, method), "format")]
            input_text = message.text.lower()
            for command in command_list:
                format = getattr(self, command).format
                try:
                    first_word = (format.split(" "))[0]
                    if input_text.find(first_word) > -1:
                        message.respond(format)
                        return True
                except:
                    pass
            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)

            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call %(mobile)s") \
                            % {'mobile': Cfg.get('developer_mobile')})

            raise
        message.was_handled = bool(self.handled)
        return self.handled

    def cleanup(self, message):
        ''' log message '''
        if bool(self.handled):
            log = MessageLog(mobile=message.peer,
                         sent_by=message.persistant_connection.reporter,
                         text=message.text,
                         was_handled=message.was_handled)
            log.save()

    def outgoing(self, message):
        '''Handle outgoing message notifications.'''
        pass

    def stop(self):
        '''Perform global app cleanup when the application is stopped.'''
        pass

    @keyword(r'takeover (\w+)')
    #uncomment this to test multiple decorators -
    # was a test for eliane by ukanga.
    #@adeco
    #@registered
    #@anotherdeco
    def reporter_http_identity(self, message, username):
        '''Gives a http identity to a httptester number of a
        registered reporter'''
        reporter = self.find_provider(message, username)
        # attach the reporter to the current connection
        if PersistantBackend.from_message(message).title == "http":
            mobile = reporter.connection().identity
            if mobile == message.persistant_connection.identity:
                message.respond(_("You already have a http identity!"))
            elif mobile[0] == "+" \
                and mobile[1:] == message.persistant_connection.identity:
                message.persistant_connection.reporter = reporter
                message.persistant_connection.save()
                message.respond(_("You now have a http identity!"))
            else:
                message.respond(_("Illegal Operation!"))
        else:
            message.respond(_("Operation not allowed under this mode!"))
        return True
    reporter_http_identity.format = "takeover [(@)username]"

    def respond_not_registered(self, message, target):
        raise HandlerFailed(_("User @%s is not registered.") % target)

    def find_provider(self, message, target):
        try:
            if re.match(r'^\d+$', target):
                reporter = Reporter.objects.get(id=target)
            else:
                reporter = Reporter.objects.get(alias__iexact=target)
            return reporter
        except models.ObjectDoesNotExist:
            # FIXME: try looking up a group
            self.respond_not_registered(message, target)
