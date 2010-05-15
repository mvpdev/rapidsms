#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django.utils.translation import ugettext as _


class CodedItem(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_codeditem'
        verbose_name = _(u"Coded Item")
        verbose_name_plural = _(u"Coded Items")
        ordering = ('type', 'code')
        unique_together = ('type', 'code')

    TYPE_DANGER_SIGN = 'DS'
    TYPE_FAMILY_PLANNING = 'FP'
    TYPE_MEDICINE = 'M'
    TYPE_COUNSELING = 'C'

    TYPE_CHOICES = (
        (TYPE_DANGER_SIGN, _(u"Danger sign")),
        (TYPE_FAMILY_PLANNING, _(u"Family planning")),
        (TYPE_MEDICINE, _(u"Medicine")),
        (TYPE_COUNSELING, _(u"Counseling topic")))

    code = models.CharField(_(u"Code"), max_length=10)
    description = models.CharField(_(u"Description"), max_length=100)
    type = models.CharField(_(u"Type"), choices=TYPE_CHOICES, max_length=2)

    def __unicode__(self):
        return u"%s: %s" % (self.code, self.description)
