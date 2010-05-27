#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from childcount.models import Encounter


def send_to_omrs(router, *args, **kwargs):
    '''Generate XFOMRS and send it to omrs'''
    Encounter.send_to_omrs()
