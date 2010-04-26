#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Measles app Models

ReportMeasles - Records cases which have received measles shot
'''

from django.db import models

from datetime import datetime

from childcount.models.general import Case
from reporters.models import Reporter


class ReportMeasles(models.Model):

    '''Records cases which have received measles shot'''

    class Meta:
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
        app_label = 'measles'
        verbose_name = "Measles Report"
        verbose_name_plural = "Measles Reports"

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    taken = models.BooleanField(db_index=True)

    def save(self, *args):
        '''Set entered_at field with current time and then save record'''
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMeasles, self).save(*args)

    def location(self):
        '''get the location of the child,case'''
        return self.case.location

    @classmethod
    def is_vaccinated(cls, case):
        '''Checks if the case/child is vaccinated

        returns True if child is Vaccinated,
         otherwise returns false
        '''
        try:
            rpt = cls.objects.filter(case=case).latest()
            if rpt:
                return rpt.taken
            return False
        except models.ObjectDoesNotExist:
            return False

    @classmethod
    def get_vaccinated(cls, reporter):
        '''Gets a list of vaccinated cases'''
        try:
            rpt = cls.objects.values('case').distinct().\
                filter(reporter=reporter)
            return rpt
        except models.ObjectDoesNotExist:
            return False

    @classmethod
    def summary_by_location(cls):
        '''gets measles summary by clinic

        counts the number of vaccinated children per clinic
        '''
        try:
            rpts = cls.objects.order_by('case__location')
            zones = []
            zcount = 0
            l = ''
            for z in rpts:
                if l == '':
                    zcount = 0
                    l = z.case.location
                if l != z.case.location:
                    zones.append((l.name, zcount))
                    zcount = 0
                    l = z.case.location
                zcount += 1
            zones.append((l.name, zcount))
            return zones
        except:
            pass
