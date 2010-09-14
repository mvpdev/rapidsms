#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django.utils.translation import ugettext as _

import reversion

from childcount.models import Patient


class HealthId(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_healthid'
        verbose_name = _(u"Health ID")
        verbose_name_plural = _(u"Health IDs")

    STATUS_GENERATED = 'G'
    STATUS_PRINTED = 'P'
    STATUS_ISSUED = 'I'
    STATUS_REVOKED = 'R'

    STATUS_CHOICES = (
        (STATUS_GENERATED, _(u"Generated")),
        (STATUS_PRINTED, _(u"Printed")),
        (STATUS_ISSUED, _(u"Issued")),
        (STATUS_REVOKED, _(u"Revoked")))

    health_id = models.CharField(_(u"Health ID"), max_length=10, unique=True)
    generated_on = models.DateTimeField(_(u"Generated on"), auto_now_add=True)
    printed_on = models.DateTimeField(_(u"Printed on"), blank=True, null=True)
    issued_on = models.DateTimeField(_(u"Issued on"), blank=True, null=True)
    revoked_on = models.DateTimeField(_(u"Revoked on"), blank=True, null=True)
    issued_to = models.ForeignKey('Patient', verbose_name=_(u"Issued to"), \
                                  blank=True, null=True)
    status = models.CharField(_(u"Status"), choices=STATUS_CHOICES, \
                              max_length=1, default=STATUS_GENERATED)

    def __unicode__(self):
        return u"%s" % self.health_id
reversion.register(HealthId)
