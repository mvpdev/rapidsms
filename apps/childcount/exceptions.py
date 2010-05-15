#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

class CCException(Exception):
    message = _(u"An error has occured.")

    def __unicode__(self):
        return self.message

class InvalidAge(CCException):
    pass

class InvalidDOB(CCException):
    pass

class AmbiguousAge(CCException):
    pass

class NotRegistered(CCException):
    def __init__(self, message=_(u"Error: You must be registered first")):
        self.message = message

class ParseError(CCException):

    def __init__(self, message=_(u"FAILED. unable to understand")):
        self.message = message

class BadValue(CCException):

    def __init__(self, message=_(u"FAILED. Bad value")):
        self.message = message

class Inapplicable(CCException):

    def __init__(self, message=_(u"FAILED. Not applicable")):
        self.message = message
