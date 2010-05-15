#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django.utils.translation import ugettext as _


class CodedItemTranslation(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_codeditemtrans'
        verbose_name = _(u"Coded Item Translation")
        verbose_name_plural = _(u"Coded Item Translations")
        ordering = ('language', 'coded_item')
        unique_together = ('coded_item', 'language')

    LANGUAGE_FRENCH = 'fr'

    LANGUAGE_CHOICES = (
        (LANGUAGE_FRENCH, _(u"French")),)

    language = models.CharField(_(u"Langauge"), choices=LANGUAGE_CHOICES, \
                                                                max_length=6)
    coded_item = models.ForeignKey('CodedItem', verbose_name=_(u"Coded Item"))
    code = models.CharField(_(u"Code"), max_length=10)
    description = models.CharField(_(u"Description"), max_length=100)

    def __unicode__(self):
        return u"%s (%s: %s)" % (self.coded_item, self.code, self.description)
