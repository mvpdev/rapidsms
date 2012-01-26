#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

class SubPeriod(object):
    def __init__(self, title, start, end):
        self.title = title
        self.start = start
        self.end = end

    def __repr__(self):
        return "<SubPeriod: %s to %s>" % (self.start, self.end)

