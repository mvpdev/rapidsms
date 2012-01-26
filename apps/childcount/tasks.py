#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

"""Tasks
"""

from operator import attrgetter
from itertools import groupby

from django.utils.translation import ugettext_lazy as _, activate

from dateutil import relativedelta
from datetime import timedelta, datetime

from celery.decorators import periodic_task
from celery.schedules import crontab

from childcount.models import ImmunizationNotification
from childcount.models import Patient
from childcount.models import CHW
from childcount.models import FeverReport
from childcount.models import FollowUpReport
from childcount.models import AppointmentReport
from childcount.models import DangerSignsReport

import childcount.helpers.chw
import childcount.helpers.site
from childcount.helpers import ranking

from childcount.indicators import message

from alerts.utils import SmsAlert


class NowPeriod(object):
    end = datetime.now()
    start = datetime.now() + timedelta(days=-30)
    title = "Past 30 Days"


@periodic_task(run_every=crontab(hour=16, minute=30, day_of_week=0))
def weekly_immunization_reminder():
    """
    Send SMS to CHW to remind them their immunization appointments, using
    the format:
    [Immunization type] date: patient_id, patient_id | date: patient_id...
    """

    # get this week appointements, grouped by CHW
    today = datetime.today()
    in_one_week = today + relativedelta.relativedelta(weeks=1)
    imms = ImmunizationNotification.objects.filter(notify_on__gte=today,
                                        notify_on__lte=in_one_week, \
                                        patient__status=Patient.STATUS_ACTIVE)\
                                           .order_by('patient__chw')
    chws = groupby(imms, attrgetter('patient.chw'))

    # send an sms to each CHW
    for chw, imms in chws:

        # change to CHW language
        activate(chw.language)

        msg = []

        # group notifications by immunization types
        imms = groupby(imms, attrgetter('immunization'))
        for imm, notifications in imms:

            # sort then group notifications by dates
            notifications = sorted(notifications, key=attrgetter('notify_on'))
            dates = groupby(notifications, attrgetter('notify_on'))

            # format id and dates
            schedules = []
            for date, ids in dates:
                ids = ', '.join(str(n.patient.health_id.upper()) for n in ids)
                schedules.append('%s: %s' % (date.strftime('%d-%m-%y'), ids))

       #join dates together, then immunizations together ans send the SMS
            msg.append((imm, ' | '.join(schedules)))

        msg_to = ' '.join('[%s] %s' % (imm, dates) for imm, dates in msg)
        alert = SmsAlert(reporter=chw, msg=msg_to)
        sms_alert = alert.send()
        sms_alert.name = u"weekly_immunization_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=7, minute=0))
def daily_fever_reminder():
    """
    Daily reminder of Fever followup cases after 48 hours.
    """
    sdate = datetime.now() + relativedelta.relativedelta(days=-3)
    #sdate = datetime.combine(sdate.date(), time(7, 0))
    edate = datetime.now() + relativedelta.relativedelta(days=-2)
    #edate = datetime.combine(edate.date(), time(7, 0))
    frs = FeverReport.objects.filter(encounter__encounter_date__gte=sdate, \
                                encounter__encounter_date__lte=edate, \
                                rdt_result=FeverReport.RDT_POSITIVE, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)\
                                .order_by('encounter__chw')
    current_reporter = None
    data = {}
    for report in frs:
        fup = FollowUpReport.objects\
            .filter(encounter__patient=report.encounter.patient, \
                encounter__encounter_date__gt=report.encounter.encounter_date)
        if fup:
            continue

        # change to CHW language
        activate(report.encounter.chw.language)

        if not current_reporter or current_reporter != report.encounter.chw:
            current_reporter = report.encounter.chw
            data[current_reporter] = []
        _msg = "%s +U F" % report.encounter.patient
        data[current_reporter].append(_msg)
        print current_reporter, _msg

    for key in data:
        msg = ', ' . join(data.get(key))
        alert = SmsAlert(reporter=key, msg=msg)
        sms_alert = alert.send()
        sms_alert.name = u"daily_fever_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=7, minute=0))
def daily_late_fever_reminder():
    """
    Daily reminder of Fever followup cases after 48 hours.
    """
    sdate = datetime.now() + relativedelta.relativedelta(days=-6)
    #sdate = datetime.combine(sdate.date(), time(7, 0))
    edate = datetime.now() + relativedelta.relativedelta(days=-3)
    #edate = datetime.combine(edate.date(), time(7, 0))
    frs = FeverReport.objects.filter(encounter__encounter_date__gte=sdate, \
                                encounter__encounter_date__lte=edate, \
                                rdt_result=FeverReport.RDT_POSITIVE, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)\
                                .order_by('encounter__chw')
    current_reporter = None
    data = {}
    for report in frs:
        fup = FollowUpReport.objects\
            .filter(encounter__patient=report.encounter.patient, \
                encounter__encounter_date__gt=report.encounter.encounter_date)
        if fup:
            continue
        if not current_reporter or current_reporter != report.encounter.chw:
            current_reporter = report.encounter.chw
            data[current_reporter] = []
        _msg = "Please follow up on %s for fever." % report.encounter.patient
        data[current_reporter].append(_msg)
        print current_reporter, _msg

    for key in data:
        msg = ', ' . join(data.get(key))
        alert = SmsAlert(reporter=key, msg=msg)
        sms_alert = alert.send()
        sms_alert.name = u"daily_late_fever_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=8, minute=0))
def daily_danger_sign_reminder():
    """
    Daily reminder of Danger Sign followup cases after 48 hours.
    Run every 6 hours during the day time.
    """
    sdate = datetime.now() + relativedelta.relativedelta(days=-6)
    #sdate = datetime.combine(sdate.date(), time(7, 0))
    edate = datetime.now() + relativedelta.relativedelta(days=-2)
    #edate = datetime.combine(edate.date(), time(7, 0))
    frs = DangerSignsReport.objects.filter(encounter__encounter_date__gte=sdate, \
                                encounter__encounter_date__lte=edate, \
                                encounter__patient__status=Patient.STATUS_ACTIVE)\
                                .order_by('encounter__chw')
    current_reporter = None
    data = {}
    for report in frs:
        fup = FollowUpReport.objects\
            .filter(encounter__patient=report.encounter.patient, \
                encounter__encounter_date__gt=report.encounter.encounter_date)
        if fup:
            continue
        if not current_reporter or current_reporter != report.encounter.chw:
            current_reporter = report.encounter.chw
            data[current_reporter] = []
        _msg = "Please follow up with %(person)s for %(signs)s" % \
            {'person': report.encounter.patient,
            'signs': report.short_summary()}
        data[current_reporter].append(_msg)
        print current_reporter, _msg

    for key in data:
        msg = ', ' . join(data.get(key))
        alert = SmsAlert(reporter=key, msg=msg)
        sms_alert = alert.send()
        sms_alert.name = u"daily_danger_sign_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=17, minute=30, day_of_week=0))
def weekly_muac_reminder():
    """
    Weekly reminder of due Muac cases, 75 days or over since last chw visit
    """
    data = {}
    for chw in CHW.objects.all():
        # muac_needing is a list of tuples of (Patient, NutritionReport)
        muac_needing = childcount.helpers.chw.kids_needing_muac(NowPeriod, chw)

        if len(muac_needing) > 0:
            data[chw] = [m[0] for m in muac_needing]

    for chw in data:

        # change to CHW language
        activate(chw.language)

        p_list = data.get(chw)
        x = 0
        y = 20
        done = False
        while not done:
            current_list = p_list[x:y]
            if not current_list:
                done = True
                break
            healthids = u' ' . join([i.health_id.upper() for i in current_list])
            msg = _(u"The following clients are due for MUAC: %(ids)s") % {
                    'ids': healthids}
            x += 20
            y += 20
            alert = SmsAlert(reporter=chw, msg=msg)
            sms_alert = alert.send()
            sms_alert.name = u"weekly_muac_reminder"
            sms_alert.save()


@periodic_task(run_every=crontab(hour=17, minute=30, day_of_week=5))
def performance_messages():
    """
    Run every Friday at 17:30 sending rankings to CHWs
    on their performance on key indicators.
    """

    indicators = [message.Sms] + list(childcount.helpers.site.key_indicators()) 
    for ind in indicators:
        print "Calculating ranks for %s" % ind
        all_ranks = ranking.compute_rankings(ind)

        for i, rank_info in enumerate(all_ranks):
            print "Sending message to %s" % rank_info['chw']

            msg = ranking.rank_message(ind, all_ranks, i)

            alert = SmsAlert(reporter=rank_info['chw'], msg=msg)
            sms_alert = alert.send()
            sms_alert.name = 'performance_messages'
            sms_alert.save()


@periodic_task(run_every=crontab(hour=18, minute=0, day_of_week=0))
def weekly_anc_visit_reminder():
    """
    Initial ANC Visit weekly reminder
    """
    alert_list = {}

    for c in CHW.objects.all():
        need_anc = childcount.helpers.chw.pregnant_needing_anc(NowPeriod, c)
        if len(need_anc) > 0:
            alert_list[c] = [t[0] for t in need_anc]

    for chw in  alert_list:

        all_chw = {}
        all_chw[chw] = chw

        """
        Get other CHW in this CHW Location and add them  Dictonary so as to 
        receive alert especially Mayange
        """
        other_chw = CHW.objects.filter(location = chw.location)
        for t in other_chw:
            if t not in all_chw:
                all_chw[t] = t

        # change to CHW language
        activate(chw.language)

        chw_list = alert_list.get(chw)
        w = ', ' . join(["%s %s" % (p.health_id.upper(), p.full_name()) \
                                for p in chw_list])
        msg = _(u"Remind the following to go for ANC at health center:" \
                " %(list)s.") % {'list': w}
        
        #Send this Message to all chw in a particular location
        for chw in all_chw: 
            alert = SmsAlert(reporter=chw, msg=msg)
            sms_alert = alert.send()
            sms_alert.name = u"weekly_anc_visit_reminder"
            sms_alert.save()


def appointment_calendar(weekday):
    '''----------- 3 days b4 apt
    monday 0      wednesday 2
    tuesday 1     thursday 3
    wednesday 2   friday 4
    thursday  3   monday 0
    friday    4   tuesday 1
    '''
    if weekday < 2:
        return weekday + 3
    else:
        return weekday - 2


def get_appointment_date(dt=datetime.today()):
    day = appointment_calendar(dt.weekday())
    return (dt + relativedelta.relativedelta(days=+3, weekday=day))


@periodic_task(run_every=crontab(hour=7, minute=30))
def appointment_reminders():
    '''Remind the chw to remind their clients of an appointment 3 week days
    before the date of appointment
    '''
    today = datetime.today().date()
    # no appointment reminder over the weekend
    if today.weekday() > 4:
        return;
    apt_date = get_appointment_date(today)
    if apt_date.weekday() == 0:
        # just in case there were appointments on saturday or sunday
        saturday = apt_date + relativedelta.relativedelta(days=-2)
        apts = AppointmentReport.objects.filter(appointment_date__lte=apt_date,\
                            appointment_date__gte=saturday,\
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            status=AppointmentReport.STATUS_OPEN)
    else:
        apts = AppointmentReport.objects.filter(appointment_date=apt_date, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            status=AppointmentReport.STATUS_OPEN)
    for apt in apts:

        # change to CHW language
        activate(apt.encounter.patient.chw.language)

        msg = _(u"Please send %(patient)s to the health center for their" \
                    " appointment on %(apt_date)s") % {
                    'patient': apt.encounter.patient, \
                    'apt_date': apt.appointment_date.strftime('%d-%m-%Y')}
        print msg
        alert = SmsAlert(reporter=apt.encounter.patient.chw, msg=msg)
        try:
            sms_alert = alert.send()
        except:
            print "Error"
        else:
            sms_alert.name = u'appointment_report_reminder'
            sms_alert.save()
            apt.sms_alert = sms_alert
            apt.save()


def appointment_defaulter_calendar(weekday):
    '''------- 2 weekdays after date of apt

    +-------------------+--------------------+
    | **Date of Appt.** | **Reminder**       |
    +-------------------+--------------------+
    | Friday 4          | Wednesday 2        |
    +-------------------+--------------------+
    | Thursday 3        | Tuesday 1          |
    +-------------------+--------------------+
    | Wednesday 2       | Monday 0           | 
    +-------------------+--------------------+
    | Tuesday 1         | Friday 4           |
    +-------------------+--------------------+
    | Monday 0          | Thursday 3         |
    +-------------------+--------------------+
    '''
    if weekday < 3:
        return weekday + 2
    else:
        return weekday - 3


def get_appointment_defaulter_date(dt=datetime.today()):
    day = appointment_defaulter_calendar(dt.weekday())
    return (dt + relativedelta.relativedelta(days=+2, weekday=day)) \
            + relativedelta.relativedelta(days=-7)


@periodic_task(run_every=crontab(hour=8, minute=0))
def appointment_defaulter_reminders():
    """Remind the chw to remind their defaulting clients of an appointment
    2 week days after the date of appointment
    """
    today = datetime.today().date()
    # no appointment reminder over the weekend
    if today.weekday() > 4:
        return;
    apt_date = get_appointment_defaulter_date(today)
    if apt_date.weekday() == 4:
        # just in case there were appointments on saturday or sunday
        sunday = apt_date + relativedelta.relativedelta(days=2)
        apts = AppointmentReport.objects.filter(appointment_date__lte=sunday,\
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            status=AppointmentReport.STATUS_OPEN)
    else:
        apts = AppointmentReport.objects.filter(appointment_date__lte=apt_date, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            status=AppointmentReport.STATUS_OPEN)
    for apt in apts:

        # change to CHW language
        activate(apt.encounter.patient.chw.language)

        msg = _(u"Please send %(patient)s to the health center on for their" \
                    " failed appointment on %(apt_date)s") % {
                    'patient': apt.encounter.patient, \
                    'apt_date': apt.appointment_date.strftime('%d-%m-%Y')}
        print msg
        alert = SmsAlert(reporter=apt.encounter.patient.chw, msg=msg)
        try:
            sms_alert = alert.send()
        except:
            print "Error"
        else:
            sms_alert.name = u'appointment_report_reminder'
            sms_alert.save()
            apt.sms_alert = sms_alert
            apt.save()
