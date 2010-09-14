#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


class CCCommand(object):
    KEYWORDS = {}
    message = None
    params = None

    def __init__(self, message, params):
        self.message = message
        self.date = self.message.date
        self.params = params

    def process(self):
        pass
