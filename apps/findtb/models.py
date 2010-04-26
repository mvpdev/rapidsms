#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.db import models
from django.utils.translation import ugettext as _

# EQA

class Batches(models.Model):

    STATUS_WAITING_DTLS = 0
    STATUS_WITH_DTLS = 1
    STATUS_AT_DLAB = 2
    STATUS_GOING_TO_NTRL = 3
    STATUS_ARRIVED_AT_NTRL = 4
    STATUS_RESULTS_COMPLETE = 5
    STATUS_GOING_TO_DTU = 6
    STATUS_BACK_AT_DTU = 7

    STATUSES = (
        (STATUS_WAITING_DTLS, _(u"XX")),
        (STATUS_WITH_DTLS, _(u"XX")),
        (STATUS_AT_DLAB, _(u"XX")),
        (STATUS_GOING_TO_NTRL, _(u"XX")),
        (STATUS_ARRIVED_AT_NTRL, _(u"XX")),
        (STATUS_RESULTS_COMPLETE, _(u"XX")),
        (STATUS_GOING_TO_DTU, _(u"XX")),
        (STATUS_BACK_AT_DTU, _(u"XX")),
    )

    #id?
    created_on = models.DateTimeField()
    #dtu = models.ForeignKey()
    number_of_slides = models.PositiveIntegerField()
    

class EQAPatient(models.Model):

    id = models.CharField(max_length=30,unique=True, primary_key=True)

class Slide(models.Model):

    RESULT_NEG = 0
    RESULT_LOW = 1
    RESULT_ONE = 2
    RESULT_TWO = 3
    RESULT_THREE = 4

    RESULTS = (
        (RESULT_NEG, _(u"Negative")),
        (RESULT_LOW, _(u"1-9 AFB")),
        (RESULT_ONE, _(u"1+")),
        (RESULT_TWO, _(u"2+")),
        (RESULT_THREE, _(u"3+")),
    )

    patient = models.ForeignKey(EQAPatient)
    sputum_number = models.PositiveIntegerField(null=False, blank=False)
    #dtu = models.ForeignKey()
    batch = models.ForeignKey(Batches)
    dtu_result = models.CharField(max_length=1, choices=RESULTS, \
                                  default=RESULT_NEG)
    district_result = models.CharField(max_length=1, choices=RESULTS, \
                                  default=RESULT_NEG)
    nrtl_result = models.CharField(max_length=1, choices=RESULTS, \
                                  default=RESULT_NEG)
    lab_result_date = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=160, null=True, blank=True)
