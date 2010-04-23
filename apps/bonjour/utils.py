#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' Bonjour i18n helpers '''

from django.conf import settings
from babel import Locale


def set_language_to(code):
    ''' sets the LANGUAGE_CODE variable with param '''
    settings.LANGUAGE_CODE = code
    return True


def set_language_to_default(router):
    ''' sets language to DEFAULT one (from bonjour config) '''
    return set_language(router.get_app('bonjour').DEFAULT_LANG)


def set_language_to_original(router):
    ''' sets language with original one (from django guess) '''
    return set_language(router.get_app('bonjour').DJANGO_LANG)


class Bonjour(object):
    ''' Holds the bonjour-defined locale '''

    @classmethod
    def lang(cls):
        ''' returns bonjour lang string '''
        return str(settings.LANGUAGE_CODE)

    @classmethod
    def locale(cls):
        ''' returns babel's locale built from bonjour lang '''
        locale = Locale.parse(settings.LANGUAGE_CODE, sep='-')
        return locale
