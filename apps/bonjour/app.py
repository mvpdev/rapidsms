#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Bonjour App

Manages end-user's locale for all Apps. '''

import rapidsms
from django.conf import settings

from bonjour.utils import *


class App (rapidsms.app.App):

    ''' Bonjour App

    Uses lang parameter from :file:`local.ini`
    Sets django locale accordingly (used by rapidsms) '''

    # default language
    DEFAULT_LANG = None
    DJANGO_LANG = None

    def configure(self, lang=None):
        ''' set configure language as global lang '''

        # store django-detected lang
        self.DJANGO_LANG = settings.LANGUAGE_CODE

        # setup provided one
        if not lang == None:
            settings.LANGUAGE_CODE = lang

        # store default lang
        self.DEFAULT_LANG = settings.LANGUAGE_CODE
