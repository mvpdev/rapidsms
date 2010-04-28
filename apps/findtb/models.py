#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group

from locations.models import Location
from reporters.models import Reporter

class Role(models.Model):
    group = models.ForeignKey(Group)
    reporter = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location)

class Patient(models.Model):

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))


    STATUS_ACTIVE = 'A'
    STATUS_INACTIVE = 'I'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _(u"Active")),
        (STATUS_INACTIVE, _(u"Inactive")))

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    #created_by = models.ForeignKey
    patient_id = models.CharField(max_length=25)
    dob = models.DateField(_(u"Date of birth"))
    estimated_dob = models.BooleanField(_(u"Estimated DOB"), default=True, \
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation"))


class Sputum(models.Model):
    class Meta:
        permissions = (
            ("can_send", "Can send"),
            ("can_receive", "Can receive")
        )

    patient = models.ForeignKey(Patient)
    location = models.ForeignKey(Location)
    date = models.DateTimeField(auto_now_add=True)
    sputum_id = models.CharField(max_length=25)
