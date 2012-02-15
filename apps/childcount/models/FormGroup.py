#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

'''ChildCount Models

FormGroup - FormGroup model
'''

import reversion
from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Reporter, PersistantBackend
from childcount.models import Encounter
from childcount.utils import get_ccforms_by_name


class FormGroup(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_frmgrp'
        verbose_name = _(u"Form Group")
        verbose_name_plural = _(u"Form Groups")

    forms = models.CharField(_(u"Forms"), max_length=150, \
                             null=True, blank=True, \
                             help_text=_(u"A comma delimited list of the " \
                                          "names of the forms successfully " \
                                          "processed"))

    entered_by = models.ForeignKey(Reporter, verbose_name=_(u"Entered by"), \
                                   null=True, blank=True, \
                                   related_name='encounters_entered')

    entered_on = models.DateTimeField(_(u"Entered on"), auto_now_add=True)

    backend = models.ForeignKey(PersistantBackend, verbose_name=_(u"Backend"))

    encounter = models.ForeignKey(Encounter, verbose_name=_(u"Encounter"), \
                                null=True, blank=True)

    def __unicode__(self):
        return u"%s (%s) %s %s" % (self.encounter, self.forms, self.backend, \
                                   self.entered_by)

    @classmethod
    def forms_summary(cls, dtstart=None):
        info = []
        if dtstart:
            frms = FormGroup.objects\
                .filter(encounter__encounter_date__year=dtstart.year,
                    encounter__encounter_date__month=dtstart.month)
        else:
            frms = FormGroup.objects
        hhforms = frms.filter(encounter__type=Encounter.TYPE_HOUSEHOLD)
        info.append({'count': hhforms.count(),
                    'name': _(u"Total Household forms")})
        forms = get_ccforms_by_name()
        for form in forms[Encounter.TYPE_HOUSEHOLD]:
            info.append({'name': form, 'count':
                frms.filter(forms__contains=form).count()})
        cforms = frms.filter(encounter__type=Encounter.TYPE_PATIENT)
        info.append({'count': cforms.count(),
                    'name': _(u"Total Consultation Forms")})
        for form in forms[Encounter.TYPE_PATIENT]:
            info.append({'name': form, 'count':
                frms.filter(forms__contains=form).count()})
        return info
