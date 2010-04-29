#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group, User
from django.db.models.signals import post_delete, pre_save

from locations.models import Location
from reporters.models import Reporter

class Role(models.Model):

    group = models.ForeignKey(Group)
    reporter = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location, blank=True, null=True)

    def __unicode__(self):
        return "%(reporter)s as %(group)s at %(location)s" % \
               {'reporter':self.reporter, 'group':self.group, \
                'location':self.location}

def Role_delete_handler(sender, **kwargs):
    '''
    Called when a Role is deleted. It checks to see if that was that reporter's
    only Role in that group and, if so, removes the User from that Group
    '''
    role = kwargs['instance']
    if not Role.objects.filter(reporter=role.reporter, \
                               group=role.group).count():
        role.reporter.groups.remove(role.group)
post_delete.connect(Role_delete_handler, sender=Role)

def Role_presave_handler(sender, **kwargs):
    '''
    Called when a Role is saved. It adds the Role's reporter (User) to the
    same group. It also removes the User from the group if they don't have
    any more Roles in that group.
    '''
    role = kwargs['instance']
    role.reporter.groups.add(role.group)
    if role.pk:
        orig_role = Role.objects.get(pk=role.pk)
        if orig_role.reporter != role.reporter:
            if Role.objects.filter(reporter=orig_role.reporter, \
                                   group=orig_role.group).count() == 1:
                orig_role.reporter.groups.remove(orig_role.group)
        else:
            if orig_role.group != role.group:
                if Role.objects.filter(reporter=role.reporter, \
                                       group=orig_role.group).count() == 1:
                    role.reporter.groups.remove(orig_role.group)
pre_save.connect(Role_presave_handler, sender=Role)


class Patient(models.Model):

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    created_by = models.ForeignKey(Reporter)
    patient_id = models.CharField(max_length=25)
    dob = models.DateField(_(u"Date of birth"))
    estimated_dob = models.BooleanField(_(u"Estimated DOB"), default=True, \
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation"))
    is_active = models.BooleanField(default=True)


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
    DTU_LAB_TECH_GROUP_NAME = 'dtu lab tech'
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


class Configuration(models.Model):

    '''Store Key/value config options'''

    description = models.CharField(_('Description'), max_length=255, \
                                   db_index=True)
    key = models.CharField(_('Key'), max_length=50, db_index=True)
    value = models.CharField(_('Value'), max_length=255, \
                             db_index=True, blank=True)

    def __unicode__(self):
        return u"%s: %s" % (self.key, self.value)

    def get_dictionary(self):
        return {'key': self.key, 'value': self.value, \
                'description': self.description}

    @classmethod
    def has_key(cls, key):
        return cls.objects.filter(key=key).count() != 0

    @classmethod
    def get(cls, key):
        '''get config value of specified key'''
        cfg = cls.objects.get(key__iexact=key)
        return cfg.value
