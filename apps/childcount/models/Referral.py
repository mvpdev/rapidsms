#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Patient - Patient model
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from reporters.models import Reporter

from childcount.models.Case import Case


class Refferral(models.Model):

    '''Holds Refferral details

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

    referral_id = models.IntegerField(db_index=True)
    case = models.ForeignKey(Case, db_index=True)
    closed_by = models.ForeignKey(Reporter, db_index=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        else:
            self.updated_at = datetime.now()
        super(Refferral, self).save(*args)
