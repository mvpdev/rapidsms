#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' USSD per-operator config holder Interface.

Stores the USSD messages to send and answers parsers
to interact with carrier's prepaid topup services'''

import re


class SimpleOperator(object):

    ''' Operator Interface.

    Provides properties and methods to store and parse USSD
    messages to/from operators'''

    CAPABILITIES = {'USSD_BALANCE': False, 'USSD_TOPUP': False}
    BALANCE_USSD = None
    TOPUP_USSD = None
    TOPUP_USSD_FMT = None

    def get_capabilities(self, feature="ALL"):
        ''' Booleans indicating if feature is supported by the operator.

        Special feature `ALL` list all features
        Returns boolean or dictionary'''
        if feature == "ALL":
            return self.CAPABILITIES
        else:
            return self.CAPABILITIES[feature]

    def get_balance(self, operator_string):
        ''' Interface to Parse operator sentence and returns the new balance.

        Returns None.'''
        return None

    def build_topup_ussd(self, card_pin):
        ''' Interface to Generate USSD message to send from voucher ID.

        Returns None.'''
        return None

    def get_amount_topup(self, operator_string):
        ''' Interface to Parse operator sentence and return amount credited.

        Returns None.'''
        return None

    def __str__(self):
        ''' Name of the Class called (Operator CodeName).

        Returns string.'''
        return self.__class__.__name__


class UnparsableUSSDAnswer(Exception):
    ''' Answer was different than expected.

    Data can't be extracted from answer. '''
    pass


class UnknownAmount(Exception):
    ''' Amount in answer is unknown.

    Either parsing failed or amount not supplied in answer. '''
    pass
