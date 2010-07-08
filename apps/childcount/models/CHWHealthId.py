#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.db import models
from django.utils.translation import ugettext as _

import reversion

from childcount.models import CHW, HealthId


class CHWHealthId(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_chwhealthid'
        verbose_name = _(u"CHW Health ID")
        verbose_name_plural = _(u"CHW Health IDs")

    health_id = models.ForeignKey('HealthId', db_index=True, unique=True,
                            verbose_name=_(u"HealthId"))
    chw = models.ForeignKey('CHW', db_index=True, blank=True, null=True,
                            verbose_name=_(u"Community health worker"))
    issued_on = models.DateTimeField(_(u"Created on"), blank=True, null=True,
                                      help_text=_(u"When the chw was issued " \
                                                   "the Health Id"))
    used = models.BooleanField(_('Used'),
                        help_text=_(u"Whether the CHW has used the HealthId"))

    def __unicode__(self):
        return u"%s" % self.health_id
reversion.register(CHWHealthId)
