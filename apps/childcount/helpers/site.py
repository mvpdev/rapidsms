#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime

from django.utils.translation import ugettext as _

from childcount.models import Patient

from childcount.indicators import fever
from childcount.indicators import follow_up
from childcount.indicators import nutrition
from childcount.indicators import pregnancy
from childcount.indicators import registration
from childcount.indicators import under_one

def key_indicators():
    return (
        nutrition.CoveragePerc,
        under_one.UnderFiveImmunizationUpToDatePerc,
        pregnancy.AncFourByMonthEightPerc,
        follow_up.OnTimePerc,
    )

def summary_stats(period):
    """Calculates a few key indicators for display
    on the dashboard.
    
    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :returns: dict
    """

    patients = Patient.objects.all()
    return {
        'num_mam_sam': nutrition.SamOrMam(period, patients),
        'num_rdt': fever.RdtPositive(period, patients),
        'num_underfive': registration.UnderFive(period, patients), 
        'num_patients': registration.Total(period, patients),
        'num_households': registration.Household(period, patients),
        'num_pregnant': pregnancy.Total(period, patients),
    }


