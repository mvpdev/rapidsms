#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models

class Hack(models.Model):
    """ Hack to get can_view permission """

    class Meta:
        app_label = 'sref'
        permissions = (
            ("can_view", "Can view"),
        )
