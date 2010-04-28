#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.contrib.auth.models import User

from locations.models import Location
from reporters.models import Reporter

from findtb.models import *
from findtb.utils import *
from findtb.exceptions import *


CLINICIAN_KEYWORD = 'cli'
DTU_LAB_TECH_KEYWORD = 'lab'
DISTRICT_TB_SUPERVISOR_KEYWORD = 'dtls'
ZONAL_TB_SUPERVISOR_KEYWORD = 'ztls'

KEYWORDS = [
    CLINICIAN_KEYWORD,
    DTU_LAB_TECH_KEYWORD,
    DISTRICT_TB_SUPERVISOR_KEYWORD,
    ZONAL_TB_SUPERVISOR_KEYWORD
]


def handle(keyword, params, message):
    if len(params) < 3:
        raise ParseError("Failed: Not enough information for " \
                         "registration You must send:\n%s LocationCode " \
                         "Surname FirstName" % keyword.upper())
    try:
        location = Location.objects.get(code=params[0])
    except Location.DoesNotExist:
        raise BadValue("Failed: %s is not a valid location code. " \
                     "Please correct and send again." % params[0].upper())

    name = ' '.join(params[1:])

    reporter = create_or_update_reporter(name, \
                                         message.persistant_connection)

    # Map keywords to auth.group names and to the creation functions
    group_mapping = {
        CLINICIAN_KEYWORD: 
            (FINDTBGroup.CLINICIAN_GROUP_NAME, create_clinician),
        DTU_LAB_TECH_KEYWORD:
            (FINDTBGroup.DTU_LAB_TECH_GROUP_NAME, create_lab_tech),
        DISTRICT_TB_SUPERVISOR_KEYWORD:
            (FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME, create_dtls),
        ZONAL_TB_SUPERVISOR_KEYWORD:
            (FINDTBGroup.ZONAL_TB_SUPERVISOR_GROUP_NAME, create_ztls)
    }

    group = FINDTBGroup.objects.get(name=group_mapping[keyword][0])
    creation_function = group_mapping[keyword][1]

    creation_function(reporter, group, location)

    reporter.save()
    message.persistant_connection.reporter = reporter
    message.persistant_connection.save()
    role = Role(location=location, reporter=reporter, group=group)
    role.save()

def create_or_update_reporter(name, persistant_connection):
    reporter = persistant_connection.reporter
    if not reporter:
        reporter = Reporter()

    surname, firstnames, alias = clean_names(name, surname_first=True)

    orig_alias = alias[:20]
    alias = orig_alias.lower()

    if alias != reporter.alias and not \
       re.match(r'%s\d' % alias, reporter.alias):
        n = 1
        while User.objects.filter(username__iexact=alias).count():
            alias = "%s%d" % (orig_alias.lower(), n)
            n += 1
        reporter.alias = alias

    reporter.first_name = firstnames
    reporter.last_name = surname
    return reporter

def create_clinician(reporter, group, location):
    pass

def create_lab_tech(reporter, group, location):
    pass

def create_dtls(reporter, group, location):
    pass

def create_ztls(reporter, group, location):
    pass
