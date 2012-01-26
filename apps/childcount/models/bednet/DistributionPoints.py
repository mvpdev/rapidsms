#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from django.db import models
from django.utils.translation import ugettext as _

import reversion

from locations.models import Location

from childcount.models import Patient, CHW


class DistributionPoints(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_distribution_points'
        verbose_name = _(u"Distribution Point")
        verbose_name_plural = _(u"Distribution Points")

    location = models.ForeignKey(Location, blank=True, null=True, \
                                 related_name='chwdistributionsite', \
                                 verbose_name=_(u"Location"), \
                                 help_text=_(u"The bednet distribution site"))
    chw = models.ManyToManyField('CHW', db_index=True,
                            verbose_name=_(u"CHW"))

    def __unicode__(self):
        return u"%s: %s" % (self.location,
            ', '.join(['%s' % chw for chw in self.chw.all()]))
