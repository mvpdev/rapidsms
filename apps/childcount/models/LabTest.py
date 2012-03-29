#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from django.db import models
from django.utils.translation import ugettext as _

import reversion


class LabTest(models.Model):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_labtest'
        verbose_name = _(u"Lab Test")
        verbose_name_plural = _(u"Lab Tests")

   
    name = models.CharField(_(u"Test Name"), max_length=30)
    code = models.CharField(_(u"Code"), max_length=10, unique=True)
    defined_results = models.BooleanField(_(u"Defined results"), \
                                        help_text=_(u"True or false: the " \
                                                     "If the results are  " \
                                                     "predifined."))
    omrs_conceptid = models.IntegerField(_(u"OMRS Concept Id"), null= True, \
                                 blank = True)

    def __unicode__(self):
        return u"%s/%s" % (self.code, self.name)
reversion.register(LabTest)
