#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django_tracking.models import TrackedItem
from findtb.models import FtbState

class Result(FtbState):
    class Meta:
        app_label = 'findtb'
    pass
