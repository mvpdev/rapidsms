#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


import urllib
import urllib2

from reporters.models import Reporter

from childcount.models.general import Case
from muac.models import ReportMalnutrition


def migrate_reporters():
    reporters = Reporter.objects.all()
    i = 0
    for reporter in reporters:
        identity = reporter.connection().identity
        info = {
            'location': reporter.location.code,
            'first_name': reporter.first_name,
            'last_name': reporter.last_name,
            'id': reporter.id
        }
        message = "mchw %(location)s %(first_name)s %(last_name)s %(id)s" % info
        response = custom_sms_send(identity, message)
        #print i + 1, ':', response
    return reporters


def setup_migration():
    #migrate reporters
    reporters = migrate_reporters()
    #setup a default household
    message = "XXXXX +NEW clsauri  default default M 28y P"
    response = custom_sms_send('+254733202270', message)
    #print response
    migrate_patients(reporters[4])


def migrate_patients(reporter):
    cases = Case.objects.filter(reporter=reporter)
    for case in cases:
        identity = reporter.connection().identity
        created_at = "%s"%case.created_at
        #make the datetime as one word
        created_at = created_at.replace(' ', 'T')
        info = {
            'identity': identity,
            'ref_id': case.ref_id,
            'location': case.location.code,
            'first_name': case.first_name,
            'last_name': case.last_name,
            'gender': case.gender,
            'dob': case.dob.strftime("%d%m%Y"),
            'hh': 'XXXXX',
            'mother': 'XXXXX',
            'status': case.status,
            'created_at': created_at,
            'estimated_dob': case.estimated_dob
        }
        message = "%(ref_id)s +new %(location)s %(first_name)s %(last_name)s "\
                    "%(gender)s %(dob)s %(hh)s %(mother)s +migrate patient "\
                    "%(estimated_dob)s %(status)s %(created_at)s" % info
        #datetime.strptime(f,"%Y-%m-%d %H:%M:%S")
        #@todo do we need to transfer birth details if they exist?
        custom_sms_send(identity, message)


def migrate_muac(patient):
    muacs = ReportMalnutrition.objects.filter(case=patient)
    for muac in muacs:
        identity = muac.reporter.connection().identity
        edema = 'edema' in [c.uid for c in muac.observed.all()]
        if not edema:
            edema = 'oedema' in [c.uid for c in muac.observed.all()]
        info = {
            "muac": muac.muac,
            "ref_id": muac.case.ref_id
        }
        message = "%(ref_id)s +MUAC %(muac)s" % info
        if edema:
            message += " Y"

        complications = [c for c in muac.observed.all() \
                         if c.uid != 'diarrhea']
        if complications:
            message += " +S"
            for comp in complications:
                code = comp.letter
                if comp.letter.lower() == 'uf':
                    #Appetite loss and not feeding seems like one and the same
                    code = 'nf'
                message += " %s" % code
        created_at = "%s"%muac.entered_at
        #make the datetime as one word
        created_at = created_at.replace(' ', 'T')

        message += " +migrate muac %(status)s %(created_at)s" % {
                    'status': muac.status,
                    'created_at': created_at
                    }
        print identity, ": ", message
        custom_sms_send(identity, message)


def custom_sms_send(identity, message):
    data = {'identity': identity, 'message': message}
    data = urllib.urlencode(data)
    url = "http://%s:%s" % ("localhost", "1338")
    req = urllib2.Request(url, data)
    stream = urllib2.urlopen(req)

    return stream.read()