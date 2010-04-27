#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class NotRegistered(Exception):
    def __init__(self, message="Sorry, only registered users "
                               "can access this program."):
        self._message = message

    @property
    def message(self):
        return self._message

class InsufficientPermissions(Exception):
    pass

class ParseError(Exception):

    def __init__(self, message="Sorry, we were unable to understand your " \
                               "message. Please check the documentation " \
                               "and try again."):
        self._message = message

    @property
    def message(self):
        return self._message


class BadValue(Exception):

    def __init__(self, message="Sorry, your message contains invalid " \
                               "information. Please check and try again "):
        self._message = message

    @property
    def message(self):
        return self._message
