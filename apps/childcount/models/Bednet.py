#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: Katembu

'''ChildCount Models

Bednet - BedNet model
'''

from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import Patient
from childcount.models.reports import CCReport

class Bednet(models.Model):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Bednet Report")
        verbose_name_plural = _(u"Bednet Distribution Reports")
