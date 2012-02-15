#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

'''ChildCount Models

PolioCampaignReport - PolioCampaignReport model
'''

from django.db import models
from django.utils.translation import ugettext as _
import reversion

import childcount.models.CHW
import childcount.models.Patient


class PolioCampaignReport(models.Model):

    '''Holds the PolioCampaignReport detail.'''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_poliocampaign'
        verbose_name = _(u"Polio Campaign Report")
        verbose_name_plural = _(u"Polio Campaign Reports")
        ordering = ('created_on', )
        unique_together = ('patient', 'phase')

    patient = models.ForeignKey('Patient', db_index=True,
                            verbose_name=_(u"Patient"))
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When reported"))
    updated_on = models.DateTimeField(auto_now=True)
    chw = models.ForeignKey('CHW', db_index=True,
                            verbose_name=_(u"Community Health Worker"))
    phase = models.PositiveSmallIntegerField(_(u"Round?"), default=1,\
                            help_text=_(u"Which round of Polio Campaign?"))
    
    def __unicode__(self):
        return u'%s: %s' % (self.patient,
                            self.created_on.strftime("%Y-%m-%d %H-%I-%S"))
reversion.register(PolioCampaignReport)
