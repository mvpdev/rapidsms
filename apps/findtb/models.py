#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group, User

from locations.models import Location
from reporters.models import Reporter

class Role(models.Model):

    group = models.ForeignKey(Group)
    reporter = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location, blank=True, null=True)

    def save(self):
        if self.reporter.user_ptr not in self.group.user_set.all():
            self.reporter.groups.add(self.group)
        super(Role, self).save() # Call the "real" save() method

    def delete(self):
        if Role.objects.filter(reporter=self.reporter, \
                               group=self.group).count() == 1:
            self.reporter.groups.remove(self.group)
        super(Role, self).delete() # Call the "real" delete() method


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
            ("send_sputum", "Can send sputum"),
            ("receive_sputum", "Can send receive")
        )

    patient = models.ForeignKey(Patient)
    location = models.ForeignKey(Location)
    date = models.DateTimeField(auto_now_add=True)
    dtu_registration_number = models.CharField(max_length=25)
    ntrl_tc_number = models.CharField(max_length=12)


class FINDTBGroup(Group):
    CLINICIAN_GROUP_NAME = 'clinician'
    DTU_LAB_TECH_GROUP_NAME = 'dtu lab technician'
    DISTRICT_TB_SUPERVISOR_GROUP_NAME = 'district tb supervisor'
    ZONAL_TB_SUPERVISOR_GROUP_NAME = 'zonal tb supervisor'

    class Meta:
        proxy = True

    def isClinician(self):
        return self.name == self.CLINICIAN_GROUP_NAME

    def isLabTech(self):
        return self.name == self.DTU_LAB_TECH

    def isDTLS(self):
        return self.name == self.DISTRICT_TB_SUPERVISOR

    def isZTLS(self):
        return self.name == self.ZONAL_TB_SUPERVISOR
