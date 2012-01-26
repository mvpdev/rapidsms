#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin


from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import DangerSign


class DangerSignTranslation(models.Model):

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Danger Sign Translation")
        verbose_name_plural = _(u"Danger Sign Translations")
        unique_together = ('dangersign', 'language')

    LANGUAGE_CHOICES = (
        ('en', _(u"English")),
        ('fr', _(u"French")))

    language = models.CharField(_(u"Language"), max_length=8, \
                                choices=LANGUAGE_CHOICES)
    code = models.CharField(_(u"Code"), max_length=10, unique=True)
    dangersign = models.ForeignKey(DangerSign, verbose_name=_(u"Danger sign"))
    description = models.CharField(_(u"Description"), max_length=255)

    def __unicode__(self):
        return u"%s: %s" % (self.code, self.description)
