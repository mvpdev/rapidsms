#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.models import CHW


class User(models.Model):

    class Meta:
        verbose_name = _(u"OpenMRS User")
        verbose_name_plural = _(u"OpenMRS Users")

    chw = models.ForeignKey(CHW, unique=True, verbose_name=_(u"CHW"))
    openmrs_id = models.PositiveIntegerField(unique=True, \
                                     verbose_name=_(u"OpenMRS ID"), \
                                     help_text=_(u"ID of that CHW in OpenMRS"))

    def __unicode__(self):
        return _(u"%(chw)s:%(id)i") % {'chw': self.chw, 'id': self.openmrs_id}
