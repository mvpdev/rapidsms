#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

Encounter - Encounter model
'''

from datetime import datetime, timedelta

import reversion
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _
from reversion.models import Version
from django.db.models import Q

from childcount.models import CHW, Patient


class Encounter(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_encounter'
        verbose_name = _(u"Encounter")
        verbose_name_plural = _(u"Encounters")

    TYPE_PATIENT = 'P'
    TYPE_HOUSEHOLD = 'H'
    TYPE_CHOICES = (
        (TYPE_PATIENT, _(u"Patient")),
        (TYPE_HOUSEHOLD, _(u"Household")))
    # Encounter validity duration in minutes
    TIMEOUT = 6 * 60

    encounter_date = models.DateTimeField(_(u"Encounter date"))

    chw = models.ForeignKey(CHW, verbose_name=_(u"CHW"))

    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"), \
                                   help_text=_(u"Patient (or head of " \
                                                "household for household " \
                                                "encounters)"))

    type = models.CharField(_(u"Type"), max_length=1, \
                                       choices=TYPE_CHOICES, \
                                       help_text=_(u"The type of encounter"))

    sync_omrs = models.NullBooleanField(_('OMRS'), null=True, blank=True)

    def inital_version(self):
        return Version.objects.get_for_object(self)[0]

    def current_version(self):
        return Version.objects.get_for_object(self).\
                                      order_by('-revision__date_created')[0]

    def modified(self):
        return Version.objects.get_for_object(self).count() > 1

    def modified_by(self):
        if not self.modified():
            return None
        return self.current_version().revision.user

    def modified_on(self):
        if not self.modified():
            return None
        return self.current_version().revision.date_created

    @property
    def is_open(self):
        ''' return true if TIMEOUT minutes has not passed since creation '''
        if self.sync_omrs == True:
            return False
        now = datetime.now()
        td = timedelta(minutes=self.TIMEOUT)
        return self.encounter_date > (now - td)

    def __unicode__(self):
        return u"%s %s: %s" % (self.get_type_display(), \
                               self.patient.health_id, \
                               self.encounter_date)

reversion.register(Encounter)
