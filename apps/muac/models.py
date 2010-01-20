#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Malnutrition App Models

ReportMalnutrition - record malnutrition measurements
'''

from django.db import models
from django.utils.translation import ugettext as _

from datetime import datetime, date

from childcount.models.general import Case
from childcount.models.reports import Observation
from reporters.models import Reporter, ReporterGroup

from muac.models import Reporter, ReporterGroup

class ReportMalnutrition(models.Model):

    '''record malnutrition measurements'''

    MODERATE_STATUS = 1
    SEVERE_STATUS = 2
    SEVERE_COMP_STATUS = 3
    HEALTHY_STATUS = 4

    STATUS_CHOICES = (
        (MODERATE_STATUS, _('MAM')),
        (SEVERE_STATUS, _('SAM')),
        (SEVERE_COMP_STATUS, _('SAM+')),
        (HEALTHY_STATUS, _("Healthy")))

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    muac = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    observed = models.ManyToManyField(Observation, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                            db_index=True, blank=True, null=True)

    class Meta:
        app_label = 'muac'
        verbose_name = "Malnutrition Report"
        verbose_name_plural = "Malnutrition Reports"
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)

    def get_dictionary(self):
        '''Get a dictionary of muac measurement report details'''
        return {
            'muac': "%d mm" % self.muac,
            'observed': ", ".join([k.name for k in self.observed.all()]),
            'diagnosis': self.get_status_display(),
            'diagnosis_msg': self.diagnosis_msg(self.reporter.language)}

    def __unicode__(self):
        return "#%d" % self.id

    def symptoms(self):
        '''get comma separated symptoms list'''
        return ", ".join([k.name for k in self.observed.all()])

    def symptoms_keys(self):
        '''get comma separated symptoms keys list'''
        return ", ".join([k.letter.upper() for k in self.observed.all()])

    def days_since_last_activity(self):
        '''Get number of days since the last muac measurement was done'''
        today = date.today()

        logs = ReportMalnutrition.objects.order_by('entered_at').\
            filter(entered_at__lte=today, case=self.case).reverse()
        if not logs:
            return ""
        return (today - logs[0].entered_at.date()).days

    def location(self):
        '''Get location of the case'''
        return self.case.location

    def name(self):
        '''Get the name of the case'''
        return "%s %s" % (self.case.first_name, self.case.last_name)

    def provider_number(self):
        '''get reporter's mobile phone number'''
        return self.reporter.connection().identity

    def diagnose(self):
        complications = [c for c in self.observed.all() \
                         if c.uid != 'edema' or c.uid != 'oedema']
        edema = 'edema' in [c.uid for c in self.observed.all()]
        if not edema:
            edema = 'oedema' in [c.uid for c in self.observed.all()]
        self.status = ReportMalnutrition.HEALTHY_STATUS
        if edema or self.muac < 110:
            if complications:
                self.status = ReportMalnutrition.SEVERE_COMP_STATUS
            else:
                self.status = ReportMalnutrition.SEVERE_STATUS
        elif self.muac < 125:
            self.status = ReportMalnutrition.MODERATE_STATUS

    def diagnosis_msg(self, lang=None):
        '''get a diagnostic message/text'''
        if lang is None:
            lang = 'en'
        msg = {}
        if self.status == ReportMalnutrition.MODERATE_STATUS:
            msg['fr'] = "MAM Enfant a besoin de nourriture supplementaire."
            msg['en'] = _("MAM Child requires supplemental feeding.")
        elif self.status == ReportMalnutrition.SEVERE_STATUS:
            msg['fr'] = "SAM Patient a besoin d aller au poste de sante"
            msg['en'] = _("SAM Patient requires OTP care")
        elif self.status == ReportMalnutrition.SEVERE_COMP_STATUS:
            msg['fr'] = "SAM+ Patient a besoin d aller immediatement au "\
                        "poste de sante"
            msg['en'] = _("SAM+ Patient requires IMMEDIATE inpatient care")
        else:
            msg['fr'] = "Enfant nest pas malnutri"
            msg['en'] = _("Child is not malnourished")

        if not lang in msg:
            lang = 'en'

        return msg[lang]

    def save(self, *args):
        '''Set entered_at field with current time and then save record'''
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMalnutrition, self).save(*args)

    def get_last_muac(self):
        '''Get the last reported muac measurements b4 this one for this case'''
        b4 = self.entered_at.replace(day=self.entered_at.day-1)

        p = ReportMalnutrition.objects.filter(case=self.case, \
                                              entered_at__lte=b4)
        if p:
            prev = p[0]
            info = prev.get_dictionary()
            change = int(float((self.muac - prev.muac) / \
                               float(self.muac)) * 100)
            info.update({'reported_date': \
                         prev.entered_at.strftime('%d.%m.%y'),
                         'percentage': change})
            return info
        return None

    @classmethod
    def count_by_provider(cls, reporter, duration_end=None, \
                          duration_start=None, status=None):
        '''Count Muac reports

        duration_start - starting date
        duration_end   - end date
        reporter - the reporter/provider
        status - MODERATE_STATUS | SEVERE_STATUS | SEVERE_COMP_STATUS
         | HEALTHY_STATUS | None

        '''
        #get reporters cases
        rcases = Case.objects.filter(reporter=reporter, \
                                     status=Case.STATUS_ACTIVE)
        if reporter is None:
            return None
        try:
            if duration_start is None or duration_end is None:
                if status is None:
                    return cls.objects.filter(reporter=reporter, \
                        case__in=rcases).\
                        values('case').distinct().count()
                else:
                    return cls.objects.filter(reporter=reporter, \
                        status=status, \
                        case__in=rcases).values('case').\
                        distinct().count()
            if status is None:
                return cls.objects.filter(entered_at__lte=duration_end, \
                        entered_at__gte=duration_start, \
                        case__in=rcases).\
                        filter(reporter=reporter).values('case').\
                        distinct().count()
            else:
                return cls.objects.filter(entered_at__lte=duration_end, \
                        entered_at__gte=duration_start, status=status, \
                        case__in=rcases).\
                        filter(reporter=reporter).values('case').\
                        distinct().count()
        except models.ObjectDoesNotExist:
            return None

    @classmethod
    def num_reports_by_case(cls, case=None):
        '''Count the number of recorded muac measurements for this case'''
        if case is None:
            return None
        try:
            return cls.objects.filter(case=case).count()
        except models.ObjectDoesNotExist:
            return None

    def get_alert_recipients(self):
        '''Get subscribers subscribed to malnutrion alerts'''
        recipients = []
        subscribers = Reporter.objects.all()
        for subscriber in subscribers:
            if subscriber.registered_self \
                and ReporterGroup.objects.get(title='muac_notifications')\
                 in subscriber.groups.only():
                recipients.append(subscriber)
        return recipients
