#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from django.db import models
from django.utils.translation import ugettext as _

import reversion

from locations.models import Location

from childcount.models import Patient, CHW


class BednetStock(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_bednetstock'
        verbose_name = _(u"Bednet Stock")
        verbose_name_plural = _(u"Bednet Stock")

    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the patient record " \
                                                   "was created"))
    updated_on = models.DateTimeField(auto_now=True)
    location = models.ForeignKey(Location, blank=True, null=True, \
                                 related_name='distributionsite', \
                                 verbose_name=_(u"Location"), \
                                 help_text=_(u"The bednet distribution site"))
    chw = models.ForeignKey('CHW', db_index=True,
                            verbose_name=_(u"Facilitator"))
    start_point = models.PositiveSmallIntegerField(_(u"Starting Quantity"),\
                            help_text=_(u"Quantity Starting Point"))
    end_point = models.PositiveSmallIntegerField(_(u"End Point Quantity"),\
                            blank=True, null=True,\
                            help_text=_(u"End Point Quantity"))
    quantity = models.PositiveSmallIntegerField(_(u"Quantity"),\
                            help_text=_(u"Quantity"))

    def __unicode__(self):
        return u"%s: Starting Quantity - %s, Quantity - %s, End Point - %s." %\
            (self.location, self.start_point, self.quantity, self.end_point)
reversion.register(BednetStock)
