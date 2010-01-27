#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Case - Case/Encounter model
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from reporters.models import Reporter

from childcount.models.Patient import Patient


class Case(models.Model):

    '''Holds Encounter details

    patient - the patient
    reporter - the reporter
    status - Open or Closed
    '''

    class Meta:
        app_label = 'childcount'

    STATUS_OPEN = 0
    STATUS_CLOSED = 1

    STATUS_CHOICES = (
        (STATUS_OPEN, _("Open")),
        (STATUS_CLOSED, _("Closed")))

    patient = models.ForeignKey(Patient, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        else:
            self.updated_at = datetime.now()
        super(Case, self).save(*args)


class CaseNote(models.Model):

    ''' Holds notes for Cases

        case - Case object
        reporter - reporter
        created_at - time created
        text - stores the note text
    '''

    case = models.ForeignKey(Case, related_name='notes', db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    text = models.TextField()

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        super(CaseNote, self).save(*args)

    class Meta:
        app_label = 'childcount'
