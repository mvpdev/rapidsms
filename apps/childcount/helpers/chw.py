#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""Helper functions that operate on or
relate to :class:`childcount.models.CHW`
objects.

"""

from datetime import timedelta

from django.utils.translation import ugettext as _

from childcount.indicators import registration
from childcount.indicators import household
from childcount.indicators import family_planning
from childcount.indicators import danger_signs
from childcount.indicators import referral
from childcount.indicators import follow_up
from childcount.indicators import pregnancy
from childcount.indicators import birth
from childcount.indicators import neonatal
from childcount.indicators import under_one
from childcount.indicators import nutrition
from childcount.indicators import fever
from childcount.indicators import medicine_given
from childcount.indicators import sanitation
from childcount.indicators import drinking_water
from childcount.indicators import bed_net_utilization_pregnancy
from childcount.indicators import bed_net_utilization
from childcount.indicators import bed_net_coverage
from childcount.indicators import school_attendance

from childcount.models import Patient
from childcount.models.reports import PregnancyReport
from childcount.models.reports import FollowUpReport
from childcount.models.reports import ReferralReport
from childcount.models.reports import NutritionReport
from childcount.models.reports import UnderOneReport


def report_indicators():
    return (
    {
        'title': _("Household"),
        'columns': [
            {'name': _("Households"), 'ind': registration.Household},
            {'name': _("Total HH Visits"), 'ind': household.Total},
            {'name': _("% HH Coverage(30 days)"), \
                                              'ind': household.CoveragePerc30},
            {'name': _("% HH Coverage(90 days)"), 'ind': household.CoveragePerc}
        ]
    },
    {
        'title': _("Family Planning"),
        'columns': [
            {'name': _("Women 15-49 Seen"), 'ind': family_planning.Women},
            {'name': _("Women Using FP"), 'ind': family_planning.Using},
            {'name': _("Women Starting FP (or Never Registered)"),
                'ind': family_planning.Starting},
        ]
    },
    {
        'title': _("Sanitation and Drinking Water"),
        'columns': [
            {'name': _("+SAN (180 days)"), \
                         'ind': sanitation.UniqueOneEightyDays},
            {'name': _("+DW (180 days)"),  \
                         'ind': drinking_water.UniqueOneEightyDays},
        ]
    },
    {
        'title': _("School Attendance"),
        'columns': [
            {'name': _("School Attendance (180 days)"), \
                         'ind': school_attendance.UniqueOneEightyDays},
        ]
    },
    {
        'title': _("Follow Up"),
        'columns': [
            {'name': _("People with DSs"), 'ind': danger_signs.Total},
            {'name': _("Cases Urgently Referred OR Treated by CHW"),
                'ind': referral.Urgent},
            {'name': _("On-Time Follow-Up Visits (between 48 and 72 hours)"), \
                'ind': follow_up.OnTime},
            {'name': _("Late Follow-Up Visits (between 72 hours and 7 days)"), \
                'ind': follow_up.Late},
            {'name': _("No Follow-Up Visits (never or after 7 days)"), \
                'ind': follow_up.Never},
        ]
    },
    {
        'title': _("Pregnancy"),
        'columns': [
            {'name': _("Pregnant Women"), 'ind': pregnancy.Total},
            {'name': _("Births"), 'ind': birth.Total},
            {'name': _("Births with 4 ANC"), 'ind': birth.WithAncFour},
            {'name': _("Babies Known Delivered in Clinic"), \
                'ind': birth.DeliveredInClinic},
            {'name': _("Neonatal Reports (within 7 days)"), \
                'ind': neonatal.WithinSevenDaysOfBirth},
        ]
    },
    {
        'title': _("Under Five"),
        'columns': [
            {'name': _("Children U5"), 'ind': registration.UnderFive},
            {'name': _("Children U5 Known Immunized"),\
                'ind': under_one.UnderFiveImmunizationUpToDate},
            {'name': _("MUACs Taken"), 'ind': nutrition.Total},
            {'name': _("Active SAM/MAM Cases"), 'ind': nutrition.SamOrMam},
        ]
    },
    {
        'title': _("Malaria"),
        'columns': [
            {'name': _("Tested RDTs"), 'ind': fever.Total},
            {'name': _("Positive RDTs"), 'ind': fever.RdtPositive},
            {'name': _("Anti-malarials Given"), 'ind': medicine_given.Antimalarial},
            {'name': _("Bednet Coverage (180days)"), \
                    'ind': bed_net_coverage.UniqueOneEightyDays},
            {'name': _("Bednet Utilization (180days)"), \
                    'ind': bed_net_utilization.UniqueOneEightyDays},
            {'name': _("Bednet Utilization Pregnancy (180days)"),  \
                    'ind': bed_net_utilization_pregnancy.UniqueOneEightyDays},
        ]
    },
    {
        'title': _("Diarrhea"),
        'columns': [
            {'name': _("U5 Diarrhea Cases"), 'ind': danger_signs.UnderFiveDiarrhea},
            {'name': _("ORS Given"), 'ind': medicine_given.Ors},
        ]
    },
)
"""The common set of :class:`indicator.Indicator` objects
used in the CHW reports.
"""


def report_indicators_two():
    return (
    {
        'title': _("Under Five"),
        'columns': [
            {'name': _("HH with under 5"), 'ind': registration.HasUnderFive},
            {'name': _("HH with under 5 visited last 30 days"), \
                                     'ind': household.UnderFiveUnique_visit},
        ]
    },
    {
        'title': _("Pregnancy"),
        'columns': [
            {'name': _("HH with pregnancy"), 'ind': registration.HasPregnancy},
            {'name': _("HH with pregnancy visited last 30 days"), \
                            'ind': household.PregnancyUnique_visit},
        ]
    },
    {
        'title': _("Neonatal"),
        'columns': [
            {'name': _("HH with neonate"), 'ind': registration.HasNeonatal},
            {'name': _("HH with neonate visited last 7 days"), \
                            'ind': household.NeonatalUnique_visit},
        ]
    },
)


def pregnant_needing_anc(period, chw):
    """Get a list of women assigned to this CHW
    who are in their 2nd or 3rd trimester of pregnancy
    who haven't had ANC visits in last 5 five weeks
    :param period: Time period
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param chw: CHW
    :type chw: :class:`childcount.models.CHW`

    :returns: list of (:class:`childcount.models.Patient`,
              last_anc_date, approx_due_date) tuples 

    """

    patients = Patient\
        .objects\
        .filter(chw=chw)\
        .pregnant_months(period.start, period.end, 4.0, 9.5,\
            False, False)

    pregs = PregnancyReport\
        .objects\
        .filter(encounter__encounter_date__gt=\
                period.end - timedelta(10 * 30.4375),
            encounter__encounter_date__lte=\
                period.end,
            encounter__patient__in=patients)\
        .order_by('-encounter__encounter_date')

    seen = []
    no_anc = []
    women = []
    for p in pregs:
        if p.encounter.patient.pk in seen:
            continue
        else:
            seen.append(p.encounter.patient.pk)

        days_ago = (period.end - p.encounter.encounter_date).days
        weeks_ago = days_ago / 7.0
        months_ago = weeks_ago / 4.0

        preg_month = p.pregnancy_month + months_ago

        months_left = 9 - preg_month
        days_left = months_left * 30.475
        due_date = period.end + timedelta(days_left)

        # Current weeks since ANC
        if p.weeks_since_anc is None:
            no_anc.append((p.encounter.patient, \
                None,\
                due_date))
        else:
            weeks_since_anc = p.weeks_since_anc + weeks_ago
            if weeks_since_anc > 5.0:
                women.append((p.encounter.patient, \
                    p.encounter.encounter_date - \
                        timedelta(7 * p.weeks_since_anc), \
                    due_date))

    women.sort(lambda x,y: cmp(x[1],y[1]))
    return (no_anc + women)

def people_without_follow_up(period, chw):
    """Get a list of people assigned to this CHW
    who were referred urgently to a clinic
    who got a late follow-up visit (3-7 days after referral) or no follow-up 
    visit (more than 7 days after referral or never)

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param chw: CHW
    :type chw: :class:`childcount.models.CHW`

    :returns: list of :class:`childcount.models.reports.ReferralReport`

    """
    elig = follow_up._eligible(period, chw.patient_set.all())
    late = []
    never = []
    for e in elig:
        f = FollowUpReport\
                .objects\
                .filter(encounter__patient__pk=e.encounter.patient.pk,
                    encounter__encounter_date__gt=\
                        e.encounter.encounter_date+follow_up.DELTA_START_ON_TIME)\
                .filter(encounter__encounter_date__lte=\
                        e.encounter.encounter_date+follow_up.DELTA_START_NEVER)

        if f.count() == 0:
            # No follow-up visit at all
            never.append(e)

        elif f.filter(encounter__encounter_date__gt=\
            e.encounter.encounter_date+follow_up.DELTA_START_LATE).count() > 0:
            # Follow-up visit was late
            late.append(e)
        else:
            # Follow-up visit was on-time
            pass

    return (late, never)

def kids_needing_muac(period, chw):
    """Get a list of MUAC-eligible patients assigned to this CHW
    who have not had a recorded MUAC in the past 90 days
    (for known healthy children) or the past 30 days
    (for known malnourished children and children with
    unknown nutrition status).

    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param chw: CHW
    :type chw: :class:`childcount.models.CHW`

    :returns: list of (:class:`childcount.models.Patient`,
              :class:`childcount.models.reports.NutritionReport`) tuples

    """

    # people eligible for MUAC
    muac_list = Patient\
        .objects\
        .filter(chw=chw)\
        .muac_eligible(period.start, period.end)\
        .order_by('encounter__patient__location__code')

    seen = []
    need_muac = []
    no_muac = []

    one_month_ago = period.end - timedelta(30.4375)
    three_months_ago = period.end - timedelta(3*30.4375)

    danger = (NutritionReport.STATUS_SEVERE, \
                    NutritionReport.STATUS_SEVERE_COMP)

    for p in muac_list:
        if p.pk in seen:
            continue
        else:
            seen.append(p.pk)

        try:
            nut = NutritionReport\
                .objects\
                .filter(encounter__patient__pk=p.pk,
                    muac__isnull=False,
                    status__isnull=False)\
                .latest('encounter__encounter_date')
        except NutritionReport.DoesNotExist:
            no_muac.append((p, None))
            continue

        if nut.status in danger and \
                nut.encounter.encounter_date < one_month_ago:
            need_muac.append((p, nut))
        elif nut.encounter.encounter_date < three_months_ago:
            need_muac.append((p, nut))
        else:
            pass

    need_muac.sort(lambda x,y:\
        cmp(x[1].encounter.encounter_date, \
            y[1].encounter.encounter_date))
    return no_muac + need_muac

def kids_needing_immunizations(period, chw):
    """Get a list of children under five years old assigned to this CHW
    who are:

    #. More than 12 months old who have no known immunization
       record or who were last known to be not fully immunized, or

    #. Less than 12 months old who have not had an immunization
       report in the past 90 days.



    :param period: Time period 
    :type period: An object with :meth:`.start` and :meth:`.end`
                  methods that each return a :class:`datetime.datetime`
    :param chw: CHW
    :type chw: :class:`childcount.models.CHW`

    :returns: :class:`django.db.models.query.QuerySet` of :class:`childcount.models.Patient`

    """


    patients = Patient\
        .objects\
        .filter(chw=chw)

    u1imms = UnderOneReport\
        .objects\
        .encounter_age(0, 365)\
        .filter(encounter__patient__in=patients,
            encounter__encounter_date__gte=period.end-timedelta(days=90),
            encounter__encounter_date__lte=period.end)\
        .latest_for_patient()\
        .filter(immunized=UnderOneReport.IMMUNIZED_YES)

    u5imms = UnderOneReport\
        .objects\
        .encounter_age(366, 5*365.25)\
        .filter(encounter__patient__in=patients,
            encounter__encounter_date__lte=period.end)\
        .latest_for_patient()\
        .filter(immunized=UnderOneReport.IMMUNIZED_YES)

    imms = (u1imms|u5imms)
    pks = [i[0] for i in imms.values_list('encounter__patient__pk')]
    print pks
    return patients\
        .under_five(period.start, period.end)\
        .exclude(pk__in=pks)\
        .order_by('location__code')

