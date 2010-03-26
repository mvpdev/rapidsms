#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import CHW


class MigrateCHW(models.Model):
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"MigrateCHW")
        verbose_name_plural = _(u"MigrateCHWs")
        ordering = ('oldid',)

    oldid = models.IntegerField(_("OldId"))
    newid = models.ForeignKey(CHW)

    def __unicode__(self):
        return u"%s: %s" % (self.oldid, self.newid)
