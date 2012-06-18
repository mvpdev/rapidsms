#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

'''ChildCount Models
OMRS Error Log
'''

import re

from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import Encounter


class OMRSErrorLog(models.Model):

    OPENMRS_UNKOWN_ERROR = 0
    OPENMRS_TRANSMISSION_ERROR = 1
    OPENMRS_XFORM_ERROR = 2
    OPENMRS_UNEXPECTEDVALUE_ERROR = 3

    ERROR_CHOICES = (
        (OPENMRS_UNKOWN_ERROR,    _("UnKnown Error")),
        (OPENMRS_TRANSMISSION_ERROR,    _("Transmission Error")),
        (OPENMRS_XFORM_ERROR,    _("XForm Module Error")),
        (OPENMRS_UNEXPECTEDVALUE_ERROR,    _("UnexpectedValueError")),
    )

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_omrserror'
        verbose_name = _(u"OMRS Error")
        verbose_name_plural = _(u"OMRS Error")

    encounter = models.ForeignKey(Encounter, verbose_name=_(u"Encounter"))
    error_type = models.PositiveSmallIntegerField(_("Error Type"), blank=False,
                                null=False, unique=False, choices=ERROR_CHOICES)
    error_message = models.TextField(_("Error message"), null=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"%s: %s" % (self.encounter, self. error_type)
