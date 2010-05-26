#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

CHW - Community Health Worker model
'''

import re

from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Reporter
from locations.models import Location
from childcount.models import Clinic


class CHW(Reporter):

    '''Community Health Worker model'''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_chw'
        verbose_name = _(u"Community Health Worker")
        verbose_name_plural = _(u"Community Health Workers")

    manager = models.ForeignKey('self', verbose_name=_(u"Manager"), \
                               blank=True, null=True)

    clinic = models.ForeignKey('Clinic', verbose_name=_(u"Clinic"), \
                               blank=True, null=True,
                               related_name='stationed_chw', \
                               help_text=_(u"The clinic this CHW reports to"))

    @classmethod
    def table_columns(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('username').verbose_name, \
            'bit': '{{object.alias}}'})
        columns.append(
            {'name': cls._meta.get_field('first_name').verbose_name, \
            'bit': '{{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('last_name').verbose_name, \
            'bit': '{{object.last_name}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name, \
            'bit': '{{object.location}}'})
        columns.append(
            {'name': _("Number of Patients"), \
            'bit': '{{_("text defined in views.py")}}'})
        columns.append(
            {'name': _("Number of Patients Under 5"), \
            'bit': '{{_("text defined in views.py")}}'})

        sub_columns = None
        return columns, sub_columns
