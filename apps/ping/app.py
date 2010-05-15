#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' Reply to `ping` messages to confirm system is up and running. '''

import re
from datetime import datetime

import rapidsms
from django.utils.translation import ugettext_lazy as _
from babel.dates import format_datetime
from bonjour.utils import *


def import_function(func):
    ''' import a function from full python path string

    returns function.'''
    if func.find('.') == -1:
        f = eval(func)
    else:
        s = func.rsplit(".", 1)
        x = __import__(s[0], fromlist=[s[0]])
        f = eval("x.%s" % s[1])
    return f


def parse_numbers(sauth):
    ''' transform a string of comma separated cell numbers into a list

    return array. '''
    nums = sauth.replace(" ", "").split(",")
    for num in nums:
        if num == "":
            nums.remove(num)
    return nums


class App (rapidsms.app.App):

    ''' Reply to `ping` messages to confirm system is up and running.

    One can specify a number or authentication function to
    limit users who can ping the system. '''

    def configure(self, auth_func=None, auth=None):
        ''' set up authentication mechanism
        configured from [ping] in rapidsms.ini '''

        # store locale
        self.locale = Bonjour.locale()

        # add custom function
        try:
            self.func = import_function(auth_func)
        except:
            self.func = None

        # add defined numbers to a list
        try:
            self.allowed = parse_numbers(auth)
        except:
            self.allowed = []

        # allow everybody trigger
        self.allow = ('*', 'all', 'true', 'True').count(auth) > 0

        # deny everybody trigger
        self.disallow = ('none', 'false', 'False').count(auth) > 0

    def handle(self, message):
        ''' check authorization and respond

        if auth contained deny string => return
        if auth contained allow string => answer
        if auth contained number and number is asking => reply
        if auth_func contained function and it returned True => reply
        else return'''

        # We only want to answer ping alone, or ping followed by a space
        # and other characters
        if not re.match(r'^ping( +|$)', message.text.lower()):
            return False

        identifier_match = re.match(r'^ping (?P<identifier>.+).*$', \
                                    message.text.lower(), re.U)
        if not identifier_match:
            identifier = False
        else:
            identifier = identifier_match.groupdict()['identifier']

        # deny has higher priority
        if self.disallow:
            return False

        # allow or number in auth= or function returned True
        if self.allow or \
            (self.allowed and self.allowed.count(message.peer) > 0) or \
            (self.func and self.func(message)):

            now = datetime.now()
            if identifier:
                message.respond(_(u"%(pingID)s on %(date)s") % \
                                {'pingID': identifier, \
                                'date': format_datetime(now, \
                                locale=self.locale)})
            else:
                message.respond(_(u"pong on %(date)s") % \
                                {'date': format_datetime(now, \
                                locale=self.locale)})
            return True
