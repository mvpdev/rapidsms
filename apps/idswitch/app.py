#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' Transform ID (number) of a recipient before it gets sent by the router '''

import rapidsms

from apps.utils import *


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


class App (rapidsms.app.App):

    ''' Transform recipient ID (number) before it gets sent by the router '''

    def configure(self, function='nothing'):
        ''' set the function to use to transform the ID

        default is internal function `nothing`'''
        try:
            self.func = import_function(function)
        except:
            self.func = nothing

    def parse(self, message):
        ''' stores ref to transformation function in idswitch property '''
        message.idswitch = self.func
