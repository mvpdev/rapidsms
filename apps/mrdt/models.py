#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''MRDT/Malaria App Models

ReportMalaria - records reported malaria rdt tests
'''

from django.db import models
from django.utils.translation import ugettext as _

from datetime import datetime, date

from childcount.models.general import Case
from childcount.models.reports import Observation
from reporters.models import Reporter, ReporterGroup


class ReportMalaria(models.Model):

    '''records reported malaria rdt tests'''

    class Meta:
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
        app_label = 'mrdt'
        verbose_name = 'Malaria Report'
        verbose_name_plural = 'Malaria Reports'

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True)
    observed = models.ManyToManyField(Observation, blank=True)

    def get_dictionary(self):
        '''Gets a dictionary of reported rdt details'''
        return {
            'result': self.result,
            'result_text': self.result and 'Y' or 'N',
            'bednet': self.bednet,
            'bednet_text': self.bednet and 'Y' or 'N',
            'observed': ', '.join([k.name for k in self.observed.all()])}

    def location(self):
        '''get location of the child'''
        return self.case.location

    def results_for_malaria_bednet(self):
        '''Get bednet results

        Return string Y if there is a bednet
        Return string N if there is no bednet
        '''
        bednet = 'N'
        if self.bednet:
            bednet = 'Y'
        return '%s' % (bednet)

    def results_for_malaria_result(self):
        '''Get Malaria results

        Return string '+' if the test was positive
        Return string '-' if the test was negative
        '''
        result = '-'
        if self.result:
            result = '+'
        return '%s' % (result)

    def name(self):
        '''Get name of child/case tested'''
        return '%s %s' % (self.case.first_name, self.case.last_name)

    def symptoms(self):
        '''Get Comma separeted list of observations'''
        return ', '.join([k.name for k in self.observed.all()])

    def provider_number(self):
        '''Get Reporters mobile phone number'''
        return self.reporter.connection().identity

    def save(self, *args):
        '''Set entered_at field with current time and then save record'''
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMalaria, self).save(*args)

    @classmethod
    def count_by_provider(cls, reporter, duration_end=None, \
                          duration_start=None):
        '''Count the number of rdt cases reported by this reporter'''
        if reporter is None:
            return None
        try:
            if duration_start is None or duration_end is None:
                return cls.objects.filter(reporter=reporter).count()
            return cls.objects.filter(entered_at__lte=duration_end, \
                        entered_at__gte=duration_start).\
                        filter(reporter=reporter).count()
        except models.ObjectDoesNotExist:
            return None

    @classmethod
    def num_reports_by_case(cls, case=None):
        '''Count the number of reported rdt tests for this child/case'''
        if case is None:
            return None
        try:
            return cls.objects.filter(case=case).count()
        except models.ObjectDoesNotExist:
            return None

    @classmethod
    def days_since_last_mrdt(cls, case):
        '''Count the number of days since the last reported rdt test was
         carried out from today'''
        today = date.today()

        logs = cls.objects.filter(entered_at__lte=today, case=case).reverse()
        if not logs:
            return ''
        return (today - logs[0].entered_at.date()).days

    def get_alert_recipients(self):
        '''Get a list of reporters/subscribers subscribed to rdt alerts'''
        recipients = []
        subscribers = Reporter.objects.all()
        for subscriber in subscribers:
            if subscriber.registered_self \
                and ReporterGroup.objects.get(title='mrdt_notifications') \
                    in subscriber.groups.only():
                recipients.append(subscriber)
        return recipients
