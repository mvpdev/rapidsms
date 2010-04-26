#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

''' Childcount Master App

Users, Locations and Cases Management '''

import re
import time
import datetime
from functools import wraps

from django.db import models
from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from goree.models import Horaire



def authenticated(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if sender property is set on message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.sender:
            return func(self, message, *args)
        else:
            message.respond(_("%(number)s is not a registered number.")
                            % {'number': message.peer})
            return True
    return wrapper


class HandlerFailed(Exception):
    ''' No function pattern matchs message '''
    pass


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"%(msg)s") \
                     % {'msg': \
                    "Sorry, only registered users can access this program."})
            return True
    return wrapper


class App(rapidsms.app.App):

    ''' ChildCount Main App

    Provides:
    User Management: join, confirm, whereami, location/loc
    Direct message: @id
    Case Management: new/nouv, cancel, innactive, activate, s/show, n/note, age
    '''

    MAX_MSG_LEN = 140
    keyword = Keyworder()
    handled = False

    def parse(self, message):

        ''' Parse incoming messages.

        flag message as not handled '''
        message.was_handled = False

    def cleanup(self, message):
        ''' log message '''
        log = MessageLog(mobile=message.peer,
                         sent_by=message.persistant_connection.reporter,
                         text=message.text,
                         was_handled=message.was_handled)
        log.save()

    def handle(self, message):
        ''' Function selector

        Matchs functions with keyword using Keyworder
        Replies formatting advices on error
        Replies on error and if no function matched '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            #message.respond(dir(self))

            command_list = [method for method in dir(self) \
                            if hasattr(getattr(self, method), 'format')]
            goree_input = message.text.lower()
            for command in command_list:
                format = getattr(self, command).format
                try:
                    first_word = (format.split(" "))[0]
                    if goree_input.find(first_word) > -1:
                        message.respond(format)
                        return True
                except:
                    pass

            message.respond(_("Sorry Unknown command: '%(msg)s...' " \
                              "Please try again") % {'msg': message.text[:20]})

            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e)

            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call %(mobile)s") \
                            % {'mobile': Cfg.get('developer_mobile')})

            elog(message.persistant_connection.reporter, message.text)
            raise
        message.was_handled = bool(self.handled)
        return self.handled

    keyword.prefix = ['horaire','hor','horaires','heures','heure','heur','h']

    @keyword(r'(\S+) (\S+)')
    def goree(self, message,depart,arrivee):
        ''' register as a user and join the system

        Format: horaire goree dakar
        [role - leave blank for CHEW] '''

        try:
            #message.respond(_("Les horaires :"))
            dep= depart.upper()
            arr= arrivee.upper()
            horaires=Horaire.objects.filter(sitedepart=dep, sitearrivee=arr).all()            
            text="Les horaires chaloupe "+depart+' '+arrivee +':'
            for h in horaires:
               
               text = text+' '+h.datedepart +','
            
            message.respond(_(text))            
            
        except:
            
            message.respond(_("Erreur Commande."))

       
