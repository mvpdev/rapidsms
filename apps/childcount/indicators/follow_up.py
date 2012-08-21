from datetime import timedelta

import numpy

from django.utils.translation import ugettext as _
from django.db import connection
from django.db.models import Q

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models.reports import CCReport
from childcount.models.reports import FollowUpReport
from childcount.models.reports import ReferralReport
from childcount.models.reports import MedicineGivenReport
from childcount.models import Patient, CodedItem

NAME = _("Follow Up")

DELTA_START_ON_TIME     = timedelta(seconds=60*60*18)   # 18 hrs
DELTA_START_LATE        = timedelta(seconds=60*60*72)   # 72 hrs
DELTA_START_NEVER       = timedelta(seconds=60*60*24*7) # 7 days

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# FUP")
    long_name   = _("Total follow-up reports this period")

    @classmethod
    def _value(cls, period, data_in):
        return FollowUpReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .count()

def _eligible(period, data_in):
    A = ReferralReport.URGENCY_AMBULANCE
    B = ReferralReport.URGENCY_BASIC
    E = ReferralReport.URGENCY_EMERGENCY

    ref = CCReport\
        .objects\
        .filter(polymorphic_ctype__name='Referral Report',
            encounter__patient__in=data_in,\
            encounter__encounter_date__range=(period.start, period.end))
    ref_a = ref.filter(referralreport__urgency=A)
    ref_b = ref.filter(referralreport__urgency=B)
    ref_e = ref.filter(referralreport__urgency=E)

    med = CCReport\
        .objects\
        .filter(polymorphic_ctype__name='Medicine Given Report',
            encounter__patient__in=data_in,\
            encounter__encounter_date__range=(period.start, period.end))

    # We need to add the excludes because django-polymorphic does not
    # allow you to union querysets with identical records
    give_am = med.filter(medicinegivenreport__medicines__code='ACT')
    give_r = med\
        .exclude(pk__in=give_am)\
        .filter(medicinegivenreport__medicines__code='R')
    give_z = med\
        .exclude(pk__in=give_am)\
        .exclude(pk__in=give_r)\
        .filter(medicinegivenreport__medicines__code='Z')

    return CCReport.objects.filter(\
        Q(pk__in=ref_a)|\
        Q(pk__in=ref_b)|\
        Q(pk__in=ref_e)|\
        Q(pk__in=give_am)|\
        Q(pk__in=give_r)|\
        Q(pk__in=give_z))

class Eligible(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "eligible"
    short_name  = _("Eligible")
    long_name   = _("Total number of referrals eligible for "\
                    "a follow-up visit during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _eligible(period, data_in).count()

def _follow_up_between(period, data_in, delta_start, delta_end):
    eligs = _eligible(period, data_in)

    count = 0
    # For each referral report that is eligible for
    # follow-up
    for elig in eligs:

        # All FollowUpReports for this patient after the referral
        f = FollowUpReport\
            .objects\
            .filter(encounter__patient__pk=elig.encounter.patient.pk,
                    encounter__encounter_date__gt=\
                        elig.encounter.encounter_date+DELTA_START_ON_TIME)
       
        # There has already been a follow-up counted for this patient,
        # so don't double-count
        if f.filter(encounter__encounter_date__lt=elig.encounter.encounter_date+delta_start):
            continue

        if f.filter(encounter__encounter_date__gte=elig.encounter.encounter_date+delta_start,
                    encounter__encounter_date__lt=elig.encounter.encounter_date+delta_end):
            count += 1
            continue
            

    return count

'''
def _follow_up_between(period, data_in, delta_start, delta_end):
    elig_rpts = _eligible(period, data_in)
    elig = [e[0] for e in elig_rpts.values_list('encounter__patient__pk')]

    f = FollowUpReport\
        .objects\
        .filter(encounter__patient__in=elig,\
            encounter__encounter_date__gte=period.start,\
            encounter__encounter_date__lte=period.end+DELTA_START_NEVER)

    count = 0
    for e in elig_rpts:
        fup_start = e.encounter.encounter_date + delta_start
        fup_end = e.encounter.encounter_date + delta_end

        #print "! %s" % e.encounter.encounter_date
        r = f.filter(encounter__patient=e.encounter.patient,\
                encounter__encounter_date__gt=fup_start, 
                encounter__encounter_date__lte=fup_end)
        if r.count():
            count += 1
        #    print "@ %s" % r[0].encounter.encounter_date

    return count
'''

class Late(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "late"
    short_name  = _("Late")
    long_name   = _("Total number of late follow-up visits "\
                    "(after 3 days but before 7 days) during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _follow_up_between(period, data_in,\
            DELTA_START_LATE, DELTA_START_NEVER)

class OnTime(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "on_time"
    short_name  = _("On-Time")
    long_name   = _("Total number of on-time follow-up visits "\
                    "between (18 and 72 hours) "\
                    "during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _follow_up_between(period, data_in,\
            DELTA_START_ON_TIME, DELTA_START_LATE)


class OnTimePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "on_time_perc"
    short_name  = _("% On-Time Follow Up")
    long_name   = _("Percentage of eligible patients getting an "\
                    "on-time follow-up visit (between "\
                    "18 and 72 hours) after visit")

    cls_num     = OnTime
    cls_den     = Eligible

class _NotOnTime(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "_not_on_time"

    cls_first   = Eligible
    cls_second  = OnTime
    
class Never(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "never"
    short_name  = _("Never")
    long_name   = _("Referral cases that were never followed "\
                    "up (or were followed after seven days)")
    cls_first   = _NotOnTime
    cls_second  = Late
    
class MedianDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = float

    slug        = "median_days"
    short_name  = _("Days")
    long_name   = _("Median number of days for follow-up")
   
    @classmethod
    def _value(cls, period, data_in):
        elig_rpts = _eligible(period, data_in)
        elig = [e[0] for e in elig_rpts.values_list('encounter__patient__pk')]

        f = FollowUpReport\
            .objects\
            .filter(encounter__patient__in=elig,\
                encounter__encounter_date__gte=period.start,\
                encounter__encounter_date__lte=period.end+DELTA_START_NEVER)

        lst = []
        for e in elig_rpts:
            fup_start = e.encounter.encounter_date + DELTA_START_ON_TIME

            r = f\
                .filter(encounter__patient=e.encounter.patient,\
                    encounter__encounter_date__gt=fup_start)\
                .order_by('encounter__encounter_date')
            
            if r.count():
                lst.append(float((r[0].encounter.encounter_date -\
                    e.encounter.encounter_date).days))
            else:
                lst.append(float('inf'))

        return numpy.median(lst)
