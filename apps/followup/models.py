#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Measles app Models

ReportMeasles - Records cases which have received measles shot
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

from datetime import datetime

from childcount.models.general import Case
from reporters.models import Reporter


class ReportImmunization(models.Model):

    '''Report for immunizations administered to a Case'''

    VACCINE_CHOICES = (
        ('BCG', _('BCG')),
        ('POLIO', _('Birth Polio')),
        ('OPV1', _('OPV1')),
        ('OPV2', _('OPV2')),
        ('OPV3', _('OPV3')),
        ('PV1', _('Pentavalent 1')),
        ('PV2', _('Pentavalent 2')),
        ('PV3', _('Pentavalent 3')),
        ('VITA', _('VITAMIN A')),
        ('M', _('Measles')))

    PERIOD_CHOICES = (
        ('0', _('At Birth')),
        ('6w', _('6 weeks')),
        ('10w', _('10 weeks')),
        ('14w', _('14 weeks')),
        ('6m', _('6 months')),
        ('9m', _('9 months')))

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    vaccine = models.CharField(max_length=10, choices=VACCINE_CHOICES)
    period = models.CharField(max_length=4, choices=PERIOD_CHOICES)

    class Meta:
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
        app_label = 'followup'
        verbose_name = "Immunization Report"
        verbose_name_plural = "Immunization Reports"

    def save(self, *args):
        '''Set entered_at field with current time and then save record'''
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportImmunization, self).save(*args)
