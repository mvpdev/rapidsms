#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.models.general import Case
from reporters.models import Reporter

from datetime import datetime


class ReportBirth(models.Model):

    '''Record Births'''

    LOCATION_CHOICES = (
        ('H', _("Home")),
        ('C', _("Health Facility")),
        ('T', _("On route to Clinic")),
        ('O', _("Other")),
    )

    case = models.ForeignKey(Case, db_index=True, null=False)
    weight = models.FloatField(db_index=True, null=False)
    where = models.CharField(max_length=1, choices=LOCATION_CHOICES)
    complications = models.CharField(max_length=255, db_index=True, null=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)

    class Meta:
        app_label = 'birth'
        verbose_name = "Birth Report"
        verbose_name_plural = "Birth Reports"
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)

    def __unicode__(self):
        return u"%(lname)s %(fname)s" % {'lname': self.case.last_name,\
                                     'fname': self.case.first_name}

    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportBirth, self).save(*args)

    def get_where(self):
        '''Return location from list of choices, default None'''
        where = dict([(k, v) for (k, v) in self.LOCATION_CHOICES])
        return where.get(self.where, None)

    def display_name(self):
        '''Return string - name of child '''
        return u"%(lname)s %(fname)s" % {'lname': self.case.last_name,\
                                     'fname': self.case.first_name}
    display_name.short_description = "Name"

    def display_dob(self):
        '''get date of birth in dd/mm/yy format'''
        return u"%(dob)s" % {'dob': self.case.dob.strftime("%d/%m/%y")}
    display_dob.short_description = "Date of Birth"
