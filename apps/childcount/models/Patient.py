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
from locations.models import Location


class Patient(models.Model):

    '''Holds the patient details, properties and methods related to it'''

    class Meta:
        app_label = 'childcount'

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0
    STATUS_DEAD = -1

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Alive')),
        (STATUS_INACTIVE, _('Relocated')),
        (STATUS_DEAD, _('Dead')))

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')))

    patient_id = models.CharField(_('Patient ID #'), null=True, \
                                  db_index=True, max_lenght=10)
    first_name = models.CharField(max_length=255, db_index=True)
    last_name = models.CharField(max_length=255, db_index=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, \
                              null=True, blank=True)
    dob = models.DateField(_('Date of Birth'), null=True, blank=True)
    estimated_dob = models.NullBooleanField(null=True, blank=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    location = models.ForeignKey(Location, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_ACTIVE)

    def generate_patient_id(self, id=None):
        """Generate the patient id string - five characters?"""
        #just a stub
        return "AB12C"

    def save(self, *args):
        """Save Patient Record

        - update the created_at and updated_at date fields
        - save a unique PID
        """
        if not self.id:
            self.created_at = self.updated_at = datetime.now()
        else:
            self.updated_at = datetime.now()
        super(Patient, self).save(*args)
        if not self.ref_id:
            #can we ensure th key generated is unique
            self.ref_id = self.generate_patient_id(self.id)
            super(Patient, self).save(*args)
