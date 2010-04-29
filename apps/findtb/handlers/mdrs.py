#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from findtb.models import *
from findtb.utils import registered

MDRS_KEYWORD = 'mdrs'

KEYWORDS = [
    MDRS_KEYWORD,
]

@registered
def handle(keyword, params, message):
    if keyword==MDRS_KEYWORD:
        pass
