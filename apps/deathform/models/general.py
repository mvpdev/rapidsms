#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Death form models

ReportDeath - Record deaths
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.models.general import Case
from reporters.models import Reporter

from datetime import datetime


class ReportDeath(models.Model):

    ''' Record deaths   '''

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')))

    LOCATION_CHOICES = (
        ('H', _('Home')),
        ('C', _('Health Facility')),
        ('T', _('On route to Clinic')),
        ('O', _('Other')))

    CAUSE_CHOICES = (
        ('P', _('Pregnancy Related')),
        ('B', _('Child Birth')),
        ('A', _('Accident')),
        ('I', _('Illness')),
        ('S', _('Sudden Death')))

    first_name = models.CharField(max_length=255, db_index=True)
    last_name = models.CharField(max_length=255, db_index=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age = models.IntegerField(db_index=True)
    dod = models.DateField(_('Date of Death'))
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    where = models.CharField(max_length=1, choices=LOCATION_CHOICES)
    cause = models.CharField(max_length=1, choices=CAUSE_CHOICES)
    description = models.CharField(max_length=255, db_index=True, null=True, \
                                   blank=True)
    case = models.ForeignKey(Case, db_index=True, null=True)

    class Meta:
        app_label = 'deathform'
        verbose_name = 'Death Report'
        verbose_name_plural = 'Death Reports'
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)

    def __unicode__(self):
        return '%s %s' % (self.last_name, self.first_name)

    def save(self, *args):
        '''set entered_at time and then save'''
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportDeath, self).save(*args)

    def age_as_text(self):
        '''return string age

         in years if age is more than a year
         or months if age is less than a year'''
        txt = ''
        if self.age >= 12 and (self.age % 12) == 0:
            txt = '%d years' % (int(self.age / 12))
        else:
            txt = '%d months' % (self.age)
        return txt

    def get_cause(self):
        '''Get cause of death full description

        dependent on CAUSE_CHOICES - key/value store for causes of death
        return string descriptive cause of death
        '''
        causes = dict([(k, v) for (k, v) in self.CAUSE_CHOICES])
        return u'%s' % causes.get(self.cause, None)

    def get_where(self):
        '''get descriptive location of death

        dependent on LOCATION_CHOICES - key/value store for location of death
        return string descriptive location of death
        '''
        where = dict([(k, v) for (k, v) in self.LOCATION_CHOICES])
        return u'%s' % where.get(self.where, None)

    def get_dictionary(self):
        '''Dictionary of dead person information'''
        return {'name': '%s %s' % (self.last_name, self.first_name),
                'age': self.age_as_text(),
                'cause': self.get_cause(),
                'where': self.get_where(),
                'dod': self.dod.strftime('%d/%m/%y')}
