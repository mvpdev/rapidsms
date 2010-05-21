#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.db import models
from django.utils.translation import ugettext as _


class Vaccine(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_vaccine'
        verbose_name = _(u"Vaccine")
        verbose_name_plural = _(u"Vaccines")
        ordering = ('code', )

    code = models.CharField(_(u"Code"), max_length=10, unique=True)
    description = models.CharField(_(u"Description"), max_length=100)

    def __unicode__(self):
        return u"%s: %s" % (self.code, self.description)
