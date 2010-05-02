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
    class Meta:
        app_label = 'findtb'

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
    class Meta:
        app_label = 'findtb'
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
    class Meta:
        app_label = 'findtb'
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

    class Meta:
        app_label = 'findtb'

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES, blank=True, null=True)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)
    created_by = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location)
    patient_id = models.CharField(max_length=25, db_index=True)
    dob = models.DateField(_(u"Date of birth"), blank=True, null=True)
    estimated_dob = models.NullBooleanField(_(u"Estimated DOB"), default=True,\
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation"))
    is_active = models.BooleanField(default=True)

    def full_name(self):
        return '%s %s' % (self.last_name, self.first_name)

    def __unicode__(self):
        if self.first_name and self.last_name:
            return self.full_name()
        return self.patient_id
    


class Specimen(models.Model):
    class Meta:
        permissions = (
            ("send_specimen", "Can send specimen"),
            ("receive_specimen", "Can send receive")
        )
        app_label = 'findtb'

    patient = models.ForeignKey(Patient)
    location = models.ForeignKey(Location)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)
    created_by = models.ForeignKey(Reporter)
    tracking_tag = models.CharField(max_length=8, unique=True, db_index=True)
    tc_number = models.CharField(max_length=12, blank=True, null=True, \
                                      db_index=True, unique=True)

    def __unicode__(self):
        string = "For %(patient)s, tracking tag %(tag)s" % \
                 {'patient':self.patient, 'tag':self.tracking_tag}
        if self.tc_number:
            string = '%s, TC#%s' % (string, self.tc_number)
        return string


class FINDTBGroup(Group):
    class Meta:
        app_label = 'findtb'
        proxy = True
    CLINICIAN_GROUP_NAME = 'clinician'
    DTU_LAB_TECH_GROUP_NAME = 'dtu lab tech'
    DISTRICT_TB_SUPERVISOR_GROUP_NAME = 'district tb supervisor'
    ZONAL_TB_SUPERVISOR_GROUP_NAME = 'zonal tb supervisor'


    def isClinician(self):
        return self.name == self.CLINICIAN_GROUP_NAME

    def isLabTech(self):
        return self.name == self.DTU_LAB_TECH

    def isDTLS(self):
        return self.name == self.DISTRICT_TB_SUPERVISOR

    def isZTLS(self):
        return self.name == self.ZONAL_TB_SUPERVISOR


class Configuration(models.Model):
    class Meta:
        app_label = 'findtb'

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

