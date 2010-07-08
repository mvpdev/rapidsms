#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Deaths - Deaths model
'''

from datetime import date

from django.db import models
from django.utils.translation import ugettext as _
import reversion

from reporters.models import Reporter
from locations.models import Location

from childcount.models import Clinic
from childcount.models import CHW
from childcount.models import Patient


class DeadPerson(models.Model):

    '''Holds the death report info for clients with no health id,
    properties and methods related to it'''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_dead_person'
        verbose_name = _(u"Dead Person")
        verbose_name_plural = _(u"Dead Persons")
        ordering = ('dod', )

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    updated_on = models.DateTimeField(auto_now=True)

    first_name = models.CharField(_(u"First name"), max_length=100)
    last_name = models.CharField(_(u"Last name"), max_length=50, \
                                 help_text=_(u"Family name or surname"))
    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GENDER_CHOICES)
    dob = models.DateField(_(u"Date of Birth"))
    dod = models.DateField(_(u"Date of Death"))
    household = models.ForeignKey('Patient', blank=True, null=True, \
                                  verbose_name=_(u"Head of House"), \
                                  help_text=_(u"The primary caregiver in " \
                                               "this person's household " \
                                               "(self if primary caregiver)"),\
                                  related_name='deads_household_member')
    chw = models.ForeignKey('CHW', db_index=True,
                            verbose_name=_(u"Community Health Worker"))
    location = models.ForeignKey(Location, blank=True, null=True, \
                                 related_name='deads_resident', \
                                 verbose_name=_(u"Location"), \
                                 help_text=_(u"The location this person " \
                                              "lives within"))
    clinic = models.ForeignKey('Clinic', blank=True, null=True, \
                               verbose_name=_(u"Health facility"), \
                               help_text=_(u"The primary health facility " \
                                            "that this patient visits"))

    mobile = models.CharField(_(u"Mobile phone number"), max_length=16, \
                              blank=True, null=True)

    def __unicode__(self):
        return u'%s %s/%s died on %s' % (self.full_name(), \
                                 self.gender, self.humanised_age(), self.dod)

    def get_dictionary(self):
        days, months = self.age_in_days_months()
        return {'full_name': '%s %s' % (self.first_name, self.last_name),
                'age': '%s' % self.humanised_age(),
                'clinic': self.clinic,
                'mobile': self.mobile,
                'chw': self.chw,
                'gender': self.gender,
                'household': self.household}

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

    def is_under_five(self):
        days, weeks, months = self.age_in_days_weeks_months()
        if months < 60:
            return True
        else:
            return False

    @classmethod
    def table_columns(cls):
        columns = []
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
reversion.register(DeadPerson)
