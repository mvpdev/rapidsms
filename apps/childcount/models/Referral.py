#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

Referral - Referral model
'''

from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import Patient
from childcount.models.reports import CCReport


class Referral(models.Model):

    '''Holds Refferral details

    patient - the patient
    reporter - the reporter
    status - Open or Closed
    '''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_referral'

    STATUS_OPEN = 0
    STATUS_CLOSED = 1

    STATUS_CHOICES = (
        (STATUS_OPEN, _(u"Open")),
        (STATUS_CLOSED, _(u"Closed")))

    ref_id = models.CharField(_(u"Referral ID"), max_length=30, db_index=True)
    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"))
    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_(u"Updated on"), auto_now=True)
    expires_on = models.DateTimeField(_(u"Expires on"), null=True, blank=True)
    description = models.TextField(_(u"Description"))
    reports = models.ManyToManyField(CCReport, verbose_name=_(u"Reports"))

    def __unicode__(self):
        return u"%s: %s" % (self.status, self.patient)
