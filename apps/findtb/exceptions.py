#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class SMSException(Exception):
    _sms = 'An error has occured.'

    @property
    def sms(self):
        return self._sms

    def __unicode__(self):
        return self.sms
    

class NotRegistered(SMSException):
    def __init__(self, sms="Sorry, only registered users " \
                           "can access this system."):
        self._sms = sms

class InsufficientPermissions(SMSException):
    pass

class NotAllowed(SMSException):

    def __init__(self, sms="Sorry, we were unable to complete your " \
                           "request. Please contact NTRL for " \
                           "assistance."):
        self._sms = sms

class ParseError(SMSException):

    def __init__(self, sms="Sorry, we were unable to understand your " \
                           "message. Please check the documentation " \
                           "and try again."):
        self._sms = sms

class BadValue(SMSException):

    def __init__(self, sms="Sorry, your message contains invalid " \
                           "information. Please check and try again "):
        self._sms = sms
