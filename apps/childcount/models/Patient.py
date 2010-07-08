#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Patient - Patient model
'''

from datetime import date

from django.db import models
from django.utils.translation import ugettext as _
import reversion

from reporters.models import Reporter
from locations.models import Location

from childcount.models import Clinic
from childcount.models import CHW


class Patient(models.Model):

    '''Holds the patient details, properties and methods related to it'''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_patient'
        verbose_name = _(u"Patient")
        verbose_name_plural = _(u"Patients")
        ordering = ('health_id', )

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0
    STATUS_DEAD = -1

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _(u"Alive")),
        (STATUS_INACTIVE, _(u"Relocated")),
        (STATUS_DEAD, _(u"Dead")))

    health_id = models.CharField(_(u"Health ID"), max_length=6, blank=True, \
                                null=True, db_index=True, unique=True, \
                                help_text=_(u"Unique Health ID"))
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    updated_on = models.DateTimeField(auto_now=True)

    first_name = models.CharField(_(u"First name"), max_length=100)
    last_name = models.CharField(_(u"Last name"), max_length=50, \
                                 help_text=_(u"Family name or surname"))
    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)
    dob = models.DateField(_(u"Date of Birth"), null=True, blank=True)
    estimated_dob = models.BooleanField(_(u"Estimated DOB"), \
                                        help_text=_(u"True or false: the " \
                                                     "date of birth is only " \
                                                     "an approximation."))
    mother = models.ForeignKey('self', blank=True, null=True, \
                               verbose_name=_(u"Mother or Guardian."), \
                               related_name='child')
    household = models.ForeignKey('self', blank=True, null=True, \
                                  verbose_name=_(u"Head of House"), \
                                  help_text=_(u"The primary caregiver in " \
                                               "this person's household " \
                                               "(self if primary caregiver)"),\
                                  related_name='household_member')
    chw = models.ForeignKey('CHW', db_index=True,
                            verbose_name=_(u"Community Health Worker"))
    location = models.ForeignKey(Location, blank=True, null=True, \
                                 related_name='resident', \
                                 verbose_name=_(u"Location"), \
                                 help_text=_(u"The location this person " \
                                              "lives within"))
    clinic = models.ForeignKey('Clinic', blank=True, null=True, \
                               verbose_name=_(u"Health facility"), \
                               help_text=_(u"The primary health facility " \
                                            "that this patient visits"))

    mobile = models.CharField(_(u"Mobile phone number"), max_length=16, \
                              blank=True, null=True)
    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES, \
                                      default=STATUS_ACTIVE)

    def is_head_of_household(self):
        return self.household == self

    def get_dictionary(self):
        days, months = self.age_in_days_months()
        return {'full_name': '%s %s' % (self.first_name, self.last_name),
                'age': '%sm' % months,
                'days': days,
                'clinic': self.clinic,
                'mobile': self.mobile,
                'status': self.STATUS_CHOICES.index(self.status),
                'chw': self.chw,
                'gender': self.gender,
                'guardian': self.guardian}

    def age_in_days_weeks_months(self):
        '''return the age of the patient in days and in months'''
        days = (date.today() - self.dob).days
        weeks = days / 7
        months = int(days / 30.4375)
        return days, weeks, months

    def years(self):
        days, weeks, months = self.age_in_days_weeks_months()
        return months / 12

    def humanised_age(self):
        '''return a string containing a human readable age'''
        days, weeks, months = self.age_in_days_weeks_months()
        if days < 21:
            return _(u"%(days)sd") % {'days': days}
        elif weeks < 12:
            return _(u"%(weeks)sw") % {'weeks': weeks}
        elif months < 60:
            return _(u"%(months)sm") % {'months': months}
        else:
            years = months / 12
            return _(u"%(years)sy") % {'years': years}

    def full_name(self):
        return ' '.join([self.first_name, self.last_name])

    def __unicode__(self):
        return u'%s %s %s/%s' % (self.health_id.upper(), self.full_name(), \
                                 self.gender, self.humanised_age())

    def is_under_five(self):
        days, weeks, months = self.age_in_days_weeks_months()
        if months < 60:
            return True
        else:
            return False

    @classmethod
    def is_valid_health_id(cls, health_id):
        MIN_LENGTH = 4
        MAX_LENGTH = 4
        BASE_CHARACTERS = '0123456789acdefghjklmnprtuvwxy'

        try:
            health_id = unicode(health_id)
            health_id = health_id.lower()
        except:
            return False

        if len(health_id) < MIN_LENGTH or len(health_id) > MAX_LENGTH:
            return False

        for char in health_id:
            if char not in BASE_CHARACTERS:
                return False

        # TODO checkbit

        return True

    @classmethod
    def table_columns(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('household').verbose_name, \
            'bit': '{{object.household.health_id}}'})
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name, \
            'bit': '{{object.health_id}}'})
        columns.append(
            {'name': _("Name"), \
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name, \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _(u"Age"), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name, \
            'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns
reversion.register(Patient)
