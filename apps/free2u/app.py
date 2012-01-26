#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Automatic sending of Zain's Me2u credit transfert

Credit a cellphone number with a fixed amount for every SMS received.'''

import rapidsms


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

    ''' Sends a Zain Uganda me2u transfer to every sms received.

    sms_cost=5
    cost_type=int
    me2u_pin=1234
    service_num=132
    auth=*
    allow_func=apps.findug.utils.allow_me2u

    Default PIN is 1234. Change by sending to 132:
    Pin[space]<old password>[space]<new password>

    http://www.ug.zain.com/en/phone-services/me2u/index.html. '''

    def configure(self, sms_cost=0, cost_type='int', me2u_pin='1234', \
                   service_num='132', allow_func=None, auth=None, \
                   idswitch_func=None):
        ''' set up Zain's me2u variables from [free2u] in rapidsms.ini '''
        # add custom function
        try:
            self.func = import_function(allow_func)
        except:
            self.func = None

        # add defined numbers to a list
        try:
            self.allowed = parse_numbers(auth)
        except:
            self.allowed = []

        # cost type (either int of float)
        try:
            self.cost_type = eval(cost_type)
        except:
            pass

        if not self.cost_type in (int, float):
            self.cost_type = int

        # allow everybody trigger
        self.allow = ('*', 'all', 'true', 'True').count(auth) > 0

        # deny everybody trigger
        self.disallow = ('none', 'false', 'False').count(auth) > 0

        # sms cost
        try:
            self.sms_cost = float(sms_cost)
        except:
            pass

        # me2u pin
        try:
            self.me2u_pin = me2u_pin
        except:
            pass

        # service number
        try:
            self.service_num = service_num
        except:
            pass

        # Edit target number
        try:
            self.idswitch_func = import_function(idswitch_func)
        except:
            self.idswitch_func = None

    def handle(self, message):
        ''' check authorization and send me2u

        if auth contained deny string => return
        if auth contained allow string => answer
        if auth contained number and number is peer => reply
        if auth_func contained function and it returned True => reply
        else return'''
        # deny has higher priority
        if self.disallow:
            return False

        # allow or number in auth= or function returned True
        if self.allow or (self.allowed and \
                          self.allowed.count(message.peer) > 0) \
                      or (self.func and self.func(message)):

            peer = self.idswitch_func(message.peer) if self.idswitch_func \
                                                    else message.peer


            # save a record of this transfer
            params = {'target': peer, \
                      'amount': self.cost_type(self.sms_cost), \
                      'password': self.me2u_pin}
            message.forward(self.service_num, \
                            "2u %(target)s %(amount)s %(password)s" % params)
            return False
