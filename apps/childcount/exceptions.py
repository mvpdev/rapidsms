#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin


"""Standard exceptions used in many
CCForm and CCComand definitions.
It is best to use these exceptions in your
own code so that users get consistent
error messages.
"""

from django.utils.translation import ugettext as _

class CCException(Exception):
    """General exception extended by 
    all other custom exceptions.
    """

    message = _(u"An error has occured.")
    """The error message to raise with the
    exception.
    """

    def __unicode__(self):
        return self.message


class InvalidAge(CCException):
    pass


class InvalidDOB(CCException):
    pass


class AmbiguousAge(CCException):
    pass


class NotRegistered(CCException):
    def __init__(self, message=_(u"Error: You must first be registered.")):
        self.message = message


class ParseError(CCException):

    def __init__(self, message=_(u"FAILED. Unable to understand message. ")):
        self.message = message


class BadValue(CCException):

    def __init__(self, message=_(u"FAILED. Bad value. ")):
        self.message = message


class Inapplicable(CCException):

    def __init__(self, message=_(u"FAILED. Not applicable.")):
        self.message = message
