#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.core.paginator import Paginator
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

def fix_migrate_ids():
    mids = MigrateIDs.objects.all()
    for m in mids:
        m.health_id = m.health_id.replace('\n', '')
        m.save()
