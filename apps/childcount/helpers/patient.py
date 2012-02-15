#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime

from django.utils.translation import ugettext as _

import bonjour

from childcount.models.reports import NutritionReport
from childcount.models.reports import UnderOneReport
from childcount.models.reports import HouseholdVisitReport

def latest_hhv_raw(period, p):
    """Look up the latest HouseholdVisitReport for this
    patient's household

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: :class:`childcount.models.reports.HouseholdVisitReport` or None
    """

    try:
        h = HouseholdVisitReport\
            .objects\
            .filter(encounter__patient=p.household, \
                encounter__encounter_date__lte=period.end)\
            .latest()
    except HouseholdVisitReport.DoesNotExist:
        return None
    return h

def latest_muac_raw(period, p):
    """Look up the latest NutritionReport for this
    patient with a non-zero MUAC value.

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: :class:`childcount.models.reports.NutritionReport` or None
    """

    try:
        n = NutritionReport\
            .objects\
            .filter(encounter__patient=p, \
                encounter__encounter_date__lte=period.end,
                muac__isnull=False,
                muac__gt=0)\
            .latest()
    except NutritionReport.DoesNotExist:
        return None
    return n

def latest_hhv_counseling(period, p):
    """Format a string containing a human-readable list
    of counseling codes 
    for this Patient's last household visit.

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: unicode
    """

    h = latest_hhv_raw(period, p)
    if h is None:
        return u"--"
   
    if h.counseling.count():
        return " ".join([c.local_code.upper() for c in h.counseling.all()])    
    else:
        return _("None")

def latest_hhv_date(period, p):
    """Format a string containing a human-readable date
    for this Patient's last household visit.

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: unicode
    """

    h = latest_hhv_raw(period, p)
    if h is None:
        return _(u"[No HHV]")
    
    return bonjour.dates.format_date(h.encounter.encounter_date, \
        format='medium')

def latest_muac_date(period, p):
    """Format a string containing a human-readable date
    and MUAC value for this Patient's last MUAC .

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: unicode
    """

    n = latest_muac_raw(period, p)
    if n is None:
        return _(u"[No MUAC]")
    
    ''' Oed = Oedema '''
    return _(u"%(date)s [%(muac)s,Oed:%(oedema)s]") % \
        {'date': bonjour.dates.format_date(n.encounter.encounter_date,\
                    format='medium'),
        'muac': n.muac or '--',
        'oedema': n.oedema}


def latest_muac(period, p):
    """Format a string containing 
    this Patient's last MUAC measurment.

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: unicode
    """
    muac = latest_muac_raw(period, p)
    if muac is not None:
        return u"%smm %s" % (muac.muac, muac.verbose_state)
    return u""

def latest_imm_report(period, kid):
    """Look up this patient's latest immunization report.

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param p: Patient
    :type p: :class:`childcount.models.Patient`
    :returns: :class:`childcount.models.reports.UnderOneReport` or None
    """
    try:
        ir = UnderOneReport\
                .objects\
                .filter(encounter__patient=kid, \
                    encounter__encounter_date__lte=period.end)\
                .latest()
    except UnderOneReport.DoesNotExist:
        return None

    return ir

