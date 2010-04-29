#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from datetime import datetime, date, timedelta

from findtb.models import *
from findtb.utils import registered, clean_names
from findtb.exceptions import ParseError, NotAllowed


MDRS_KEYWORD = 'mdrs'

KEYWORDS = [
    MDRS_KEYWORD,
]

INFO_STRING = "Failed. Check documentation. Try " \
              "again by sending:\n PatientRegistration Surname FirstName " \
              "Age Gender"

@registered
def handle(keyword, params, message):
    if keyword==MDRS_KEYWORD:
        lab_tech = FINDTBGroup.objects.get(name=\
                                        FINDTBGroup.DTU_LAB_TECH_GROUP_NAME)
        reporter = message.persistant_connection.reporter
        try:
            location = Role.objects.get(group=lab_tech, \
                                reporter=reporter).location
        except Role.MultipleObjectsReturned:
            raise Exception("Lab tech %s registered at multiple DTUs" % \
                            reporter)
        except Role.DoesNotExist:
            raise NotAllowed("You do not have permission to register MDRS " \
                             "samples.")

        if len(params) < 5:
            raise ParseError(INFO_STRING)

        sputum = Sputum()
        patient = Patient()
        patient.created_by = sputum.created_by = message.reporter
        patient.location = sputum.location = location

        text = ' '.join(params)
        match = re.match(r'^(\d+)[ -./\\_]+(\d{2})(.*)',text)
        if not match:
            raise ParseError("Failed: Invalid Patient registration number. " \
                             "Should be in the " \
                             "format XXXX/YY where XXXX is a number and YY " \
                             "is the last two digits of year when patient " \
                             "was registered.")

        patient.patient_id = '%04d/%s' % \
                                    (int(match.groups()[0]), match.groups()[1])
        text = match.groups()[2]

        note = ''
        match = re.match(r'(?P<text>.*)\+\s?n(ote)?\s*(?P<note>.*)', text)
        if match:
            note = match.groupdict()['note']
            text = match.groupdict()['text']

        params = text.split()
        if len(params) < 4:
            raise ParseError(INFO_STRING)

        gender = params.pop().upper()
        if not re.match('^[MF]$', gender):
            raise ParseError(INFO_STRING)
        patient.gender = gender
        
        age = params.pop()
        if age.isdigit() and int(age) < 110:
            age = int(age)
        else:
            raise ParseError(INFO_STRING)

        WEEKS_IN_YEAR = 52.1774
        patient.dob = date.today() - timedelta(weeks=WEEKS_IN_YEAR*(age+.5))

        flat_name = ' '.join(params)
        patient.last_name, patient.first_name, a = \
                                    clean_names(flat_name, surname_first=True)

        sputum.sputum_id = "%s-%s" % \
                     (patient.patient_id, datetime.today().strftime("%d%m%y"))

        patient.save()
        sputum.patient = patient
        sputum.save()
        message.respond(sputum.sputum_id)
