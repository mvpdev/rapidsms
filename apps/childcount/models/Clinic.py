#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

Clinic - Clinic model
'''

from django.utils.translation import ugettext as _

from locations.models import Location


class Clinic(Location):

    '''Clinic model'''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_clinic'
        verbose_name = _(u"Clinic")
        verbose_name_plural = _(u"Clinics")
