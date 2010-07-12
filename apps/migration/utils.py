#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from models import *

from childcount.models import Patient


def match_patient_status(mid):

    '''Check that the correct patient status is migrated'''

    try:
        patient = Patient.objects.get(health_id=mid.health_id)
        case = Case.objects.get(ref_id=mid.oldid)
        if case.STATUS_ACTIVE == patient.STATUS_ACTIVE or \
                case.STATUS_INACTIVE == patient.STATUS_INACTIVE or \
                case.STATUS_DEAD == patient.STATUS_DEAD:
            return True
        else:
            return False
    except (Patient.DoesNotExist, Case.DoesNotExist):
        print mid, " Not Migrated"
        return False


def paged_patients(page=1):
    '''Paged Patients List'''

    #migrated patients
    mps_list = MigrateIDs.objects.exclude(oldid=None)
    paginator = Paginator(mps_list, 500)

    on_last_page = False
    try:
        mps = paginator.page(page)
    except (EmptyPage, InvalidPage):
        mps = paginator.page(paginator.num_pages)
        on_last_page = True

    return mps.object_list, on_last_page, paginator.num_pages


def paged_mrdts(page=1):
    '''Paged Patients List'''

    #migrated patients
    mps_list = ReportMalaria.objects.all()
    paginator = Paginator(mps_list, 500)

    on_last_page = False
    try:
        mps = paginator.page(page)
    except (EmptyPage, InvalidPage):
        mps = paginator.page(paginator.num_pages)
        on_last_page = True

    return mps.object_list, on_last_page, paginator.num_pages


def paged_muacs(page=1):
    '''Paged Patients List'''

    #migrated patients
    mps_list = ReportMalnutrition.objects.all()
    paginator = Paginator(mps_list, 1500)

    on_last_page = False
    try:
        mps = paginator.page(page)
    except (EmptyPage, InvalidPage):
        mps = paginator.page(paginator.num_pages)
        on_last_page = True

    return mps.object_list, on_last_page, paginator.num_pages


def check_mismatchs():
    done = False
    page = 1
    while (done == False):
        mids, done, npages = paged_patients(page)
        page += 1
        if page > npages and not done:
            done = True
        matched = 0
        for mid in mids:
            if match_patient_status(mid):
                matched += 1
        print matched, "/", len(mids)


def move_rdt(rdt_list):
    c = 0
    for rdt in rdt_list:
        m = migrate_mrdt(rdt)
        if m:
            c += 1
    print c, "/", len(rdt_list)
    return "%s/%s" % (c,  len(rdt_list))


def move_rdts():
    done = False
    page = 1
    summaries = []
    while (done == False):
        mids, done, npages = paged_mrdts(page)
        page += 1
        if page > npages and not done:
            done = True
        s = move_rdt(mids)
        summaries.append(s)
        print s
    print ""
    print "------------xxxxxxxxxxxx-----------------"
    for summary in summaries:
        print summary


def move_muac(muac_list):
    c = 0
    for muac in muac_list:
        m = migrate_muac(muac)
        if m:
            c += 1
    print c, "/", len(muac_list)
    return "%s/%s" % (c,  len(muac_list))


def reset_muac_progress():
    mp = MuacProgress.objects.get(id=1)
    print mp.page
    mp.page = 1
    mp.save()
    print "Muac Progress reset"


def move_muacs():
    done = False
    try:
        mp = MuacProgress.objects.get(id=1)
    except MuacProgress.DoesNotExist:
        mp = MuacProgress()
        mp.page = 1
        mp.save()
    page = mp.page
    summaries = []
    c = 0
    while (done == False and c < 3):
        mids, done, npages = paged_muacs(page)
        page += 1
        c += 1
        if page > npages and not done:
            done = True
        s = move_muac(mids)
        summaries.append(s)
        print page, len(mids)
    mp.page = page
    mp.save()
    print ""
    print "------------xxxxxxxxxxxx-----------------"
    for summary in summaries:
        print summary


def fix_migrate_ids():
    mids = MigrateIDs.objects.all()
    for m in mids:
        m.health_id = m.health_id.replace('\n', '')
        m.save()
