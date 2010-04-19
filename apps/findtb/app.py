#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

import rapidsms

class App(rapidsms.app.App):
    pass

    def handle(self, message):
        raw = message.text
        print u"HANDLE raw: %s" % raw
        text = raw.decode('utf8')
        print u"HANDLE FINTB: %s" % text
        if text == u"اثغ":
            message.respond(u"شكرا")
            return True
