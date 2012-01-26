#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Operator-specific USSD dialogs.

Stores the USSD messages to send and answers parsers
to interact with carrier's prepaid topup services '''

from apps.simpleoperator.simpleoperator import *

# Following is a list of operators
# all subclassing SimpleOperator

## GHANA


class MTNGhana(SimpleOperator):

    ''' MTN in Ghana.

    Provides properties and methods to store and parse USSD
    messages to/from operator. '''

    CAPABILITIES = {'USSD_BALANCE': True, 'USSD_TOPUP': True}
    BALANCE_USSD = "*124#"
    TOPUP_USSD = "*125*"
    TOPUP_USSD_FMT = "%s%s#"

    def get_balance(self, operator_string):
        ''' Grab balance from operator answer.

        returns float.'''
        #Your Balance is 5.84 Ghana Cedi(s),and your bonus account is 0.00.
        #Simply keep your line active before Sep 25 2009 to keep your
        # number forever.
        try:
            balance_grp = re.search( \
                                'Your Balance is ([0-9\.]+) Ghana Cedi\(s\)', \
                                operator_string)
            return float(balance_grp.groups()[0])
        except:
            raise UnparsableUSSDAnswer(operator_string)

    def build_topup_ussd(self, card_pin):
        ''' Generates USSD message including voucher ID.

        Returns string.'''
        return self.TOPUP_USSD_FMT % (self.TOPUP_USSD, card_pin)

    def get_amount_topup(self, operator_string):
        ''' Retrieve amount toped-up from operator answer.

            Returns float.'''
        #You have recharged 5.50 GHC.New Balance is 5.84 GHC remember to start
        # with 024 or 054 when you call an MTN number.Enjoy 40% discount
        # with MTN Family&Friends
        try:
            amount_grp = re.search('You have recharged ([0-9\.]+)', \
                                   operator_string)
            return float(amount_grp.groups()[0])
        except:
            raise UnparsableUSSDAnswer(operator_string)

## MALI


class Malitel(SimpleOperator):

    ''' Malitel in Mali.

    Provides properties and methods to store and parse USSD
    messages to/from operator'''

    CAPABILITIES = {'USSD_BALANCE': True, 'USSD_TOPUP': True}
    BALANCE_USSD = "*101#"
    TOPUP_USSD = "*102#"
    TOPUP_USSD_FMT = "%s%s#"

    def get_balance(self, operator_string):
        ''' Grab balance from operator answer

        returns float.'''
        #Votre solde est de 0 FCFA valable jusqu au 31.12.2029. Votre delai
        # de grace arrive a expiration le 31.03.2030
        try:
            balance_grp = re.search('Votre solde est de ([0-9\.]+) FCFA', \
                                    operator_string)
            return float(balance_grp.groups()[0])
        except:
            raise UnparsableUSSDAnswer(operator_string)

    def build_topup_ussd(self, card_pin):
        ''' Generates USSD message including voucher ID.

        Returns string.'''
        return self.TOPUP_USSD_FMT % (self.TOPUP_USSD, card_pin)

    def get_amount_topup(self, operator_string):
        ''' Retrieve amount toped-up from operator answer.

        Returns float.'''
        #VOUS AVEZ APPROVISIONNE VOTRE COMPTE DE 1000 FCFA.Votre solde est de
        # 1000 FCFA valable jusqu au 10.10.2009.
        try:
            amount_grp = re.search( \
                   'VOUS AVEZ APPROVISIONNE VOTRE COMPTE DE ([0-9\.]+) FCFA', \
                   operator_string)
            return float(amount_grp.groups()[0])
        except:
            raise UnparsableUSSDAnswer(operator_string)

## UGANDA


class ZainUganda(SimpleOperator):

    ''' Zain in Uganda.

    Provides properties and methods to store and parse USSD
    messages to/from operator'''

    CAPABILITIES = {'USSD_BALANCE': True, 'USSD_TOPUP': True}
    BALANCE_USSD = "*131#"
    TOPUP_USSD = "*130*"
    TOPUP_USSD_FMT = "%s%s#"

    def get_balance(self, operator_string):
        ''' Grab balance from operator answer.

        returns float.'''
        #Your account balance is 1000 Ushs. blabla
        try:
            balance_grp = re.search( \
                                  'Your account balance is ([0-9\.]+) Ushs.', \
                                  operator_string)
            return float(balance_grp.groups()[0])
        except:
            raise UnparsableUSSDAnswer(operator_string)

    def build_topup_ussd(self, card_pin):
        ''' Generates USSD message including voucher ID.

        Returns string.'''
        return self.TOPUP_USSD_FMT % (self.TOPUP_USSD, card_pin)

    def get_amount_topup(self, operator_string):
        ''' Retrieve amount toped-up from operator answer.

        Returns float.'''
        #Your account balance is 5270Ushs.
        try:
            amount_grp = re.search( \
                                  'Your account balance is ([0-9\.]+) Ushs.', \
                                  operator_string)
            raise UnknownAmount(amount_grp)
        except:
            raise UnparsableUSSDAnswer(operator_string)


class MTNUganda(SimpleOperator):

    ''' MTN in Uganda.

    Provides properties and methods to store and parse USSD
    messages to/from operator'''

    CAPABILITIES = {'USSD_BALANCE': True, 'USSD_TOPUP': True}
    BALANCE_USSD = "*156#"
    TOPUP_USSD = "*155*"
    TOPUP_USSD_FMT = "%s%s#"

    def get_balance(self, operator_string):
        ''' Grab balance from operator answer.

        returns float.'''
        #Your account balance is UGX 9430.
        try:
            balance_grp = re.search( \
                                  'Your account balance is UGX ([0-9\.]+)\.', \
                                  operator_string)
            return float(balance_grp.groups()[0])
        except:
            raise UnparsableUSSDAnswer(operator_string)

    def build_topup_ussd(self, card_pin):
        ''' Generates USSD message including voucher ID.

        Returns string.'''
        return self.TOPUP_USSD_FMT % (self.TOPUP_USSD, card_pin)

    def get_amount_topup(self, operator_string):
        ''' Retrieve amount toped-up from operator answer.

        Returns float.'''
        #Your account balance is 5270Ushs.
        try:
            amount_grp = re.search( \
                                 'Your account balance is ([0-9\.]+) Ushs\.', \
                                 operator_string)
            raise UnknownAmount(amount_grp)
        except:
            raise UnparsableUSSDAnswer(operator_string)
