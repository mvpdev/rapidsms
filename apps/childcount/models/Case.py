#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

Case - Case/Encounter model
'''

from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import Patient
from childcount.models.reports import CCReport


class Case(models.Model):

    '''Holds Encounter details

    patient - the patient
    reporter - the reporter
    status - Open or Closed
    '''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_case'
        verbose_name = _(u"Case")
        verbose_name_plural = _(u"Cases")
        get_latest_by = 'created_on'
        ordering = ('-created_on',)

    STATUS_OPEN = 0
    STATUS_CLOSED = 1

    STATUS_CHOICES = (
        (STATUS_OPEN, _(u"Open")),
        (STATUS_CLOSED, _(u"Closed")))

    TYPE_PREGNANCY = 0
    TYPE_MALNUTRITION = 1
    TYPE_FEVER = 2
    TYPE_DIARRHEA = 3

    TYPE_CHOICES = (
        (TYPE_PREGNANCY, _(u"Pregnancy")),
        (TYPE_MALNUTRITION, _(u"Malnutrition")),
        (TYPE_FEVER, _(u"Fever")),
        (TYPE_DIARRHEA, _(u"Diarrhea")))

    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"), \
                                db_index=True)

    type = models.SmallIntegerField(_(u"Type of case"), choices=TYPE_CHOICES)

    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)

    reports = models.ManyToManyField(CCReport, verbose_name=_(u"Reports"))

    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)

    updated_on = models.DateTimeField(_(u"Updated on"), auto_now=True)

    expires_on = models.DateTimeField(_(u"Expires on"), null=True, blank=True)
