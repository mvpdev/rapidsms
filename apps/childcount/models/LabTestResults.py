#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from django.db import models
from django.utils.translation import ugettext as _

from childcount.models import LabTest

import reversion


class LabTestResults(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_labtestresults'
        verbose_name = _(u"Lab Test Result")
        verbose_name_plural = _(u"Lab Test Results")

   
    test = models.ForeignKey('LabTest', verbose_name=_(u"Lab Test"))
    result_type = models.CharField(_(u"Results Type"), max_length=30, \
                                 blank=True , null= True)
    units = models.CharField(_(u'Units '), max_length=20, blank = True, null= True)
    ref_range = models.CharField(_(u"Results Range "), max_length=15, \
                                     blank=True , null= True)
    omrs_conceptid = models.IntegerField(_(u"OMRS Concept Id"), max_length=15, \
                                 blank = True, null= True)

    def __unicode__(self):
        return u"%s: %s" % (self.test, self.result_type)
reversion.register(LabTestResults)
