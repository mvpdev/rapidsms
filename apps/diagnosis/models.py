#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Diagnosis Models

Lab - Stores key/value lab codes
LabDiagonsis - Stores diagnosed Lab results
DiagnosisCategory - Maintains Diagnosis Categories
Diagnosis - Stores Diagnosis codes
ReportDiagnosis - Stores Diagnosis reports
'''

from django.db import models
from datetime import datetime

from childcount.models.general import Case
from reporters.models import Reporter


class Lab(models.Model):

    '''Stores key/value lab codes'''

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'diagnosis'
        ordering = ('code',)


class LabDiagnosis(models.Model):

    '''Stores diagnosed Lab results'''

    lab = models.ForeignKey(Lab)
    diagnosis = models.ForeignKey('ReportDiagnosis')
    amount = models.IntegerField(blank=True, null=True)
    result = models.BooleanField(blank=True)

    def __unicode__(self):
        return "%s, %s - %s" % (self.lab, self.diagnosis, self.amount)

    class Meta:
        app_label = 'diagnosis'


class DiagnosisCategory(models.Model):

    '''Maintains Diagnosis Categories'''

    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'diagnosis'
        ordering = ('name',)


class Diagnosis(models.Model):

    '''Stores Diagnosis codes'''

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    category = models.ForeignKey(DiagnosisCategory)
    mvp_code = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)

    def __unicode__(self):
        return self.mvp_code

    class Meta:
        app_label = 'diagnosis'
        ordering = ('code',)
        verbose_name = "Diagnosis Code"
        verbose_name_plural = "Diagnosis Codes"


class ReportDiagnosis(models.Model):

    '''Stores Diagnosis reports'''

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    diagnosis = models.ManyToManyField(Diagnosis)
    lab = models.ManyToManyField(Lab, through=LabDiagnosis)
    text = models.TextField()
    entered_at = models.DateTimeField(db_index=True)

    def __unicode__(self):
        return self.case

    class Meta:
        verbose_name = "Diagnosis Report"
        app_label = 'diagnosis'

    def save(self, *args):
        '''Set entered_at field with current time and then save record'''
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportDiagnosis, self).save(*args)

    def get_dictionary(self):
        '''Get a dictionary of a diagnosis report details'''
        extra = []
        for ld in LabDiagnosis.objects.filter(diagnosis=self):
            if ld.amount:
                extra.append('%s %s' % (ld.lab.code, ld.amount))
            else:
                extra.append('%s%s' % (ld.lab.code, ld.result and '+' or '-'))

        return {
            'diagnosis': ', '.join([str(d) for d in self.diagnosis.all()]),
            'labs': ', '.join([str(d) for d in self.lab.all()]),
            'labs_text': ', '.join(extra)}
