#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db.models import Q

from findtb.models import *
from findtb.libs.utils import registered
from findtb.exceptions import *

NOTICE_KEYWORD = 'notice'

KEYWORDS = [
    NOTICE_KEYWORD,
]

@registered
def handle(keyword, params, message):
    if keyword==NOTICE_KEYWORD:
        reporter = message.persistant_connection.reporter

        lab_group = FINDTBGroup.objects.get(name= \
                                           FINDTBGroup.DTU_LAB_TECH_GROUP_NAME)
        clinician_group = FINDTBGroup.objects.get(name= \
                                           FINDTBGroup.CLINICIAN_GROUP_NAME)
        first_group = FINDTBGroup.objects.get(name= \
                            FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME)
        eqa_group = FINDTBGroup.objects.get(name= \
                            FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME)
        try:
            role = Role.objects.get(Q(group=lab_group) | \
                                    Q(group=clinician_group) | \
                                    Q(group=first_group) | \
                                    Q(group=eqa_group), \
                                    reporter=reporter)
        except Role.DoesNotExist:
            raise NotAllowed(u"You must be registered as a DTU Lab " \
                              "Technician or Clinican to send a " \
                              "notice.")

        if len(params) == 0:
            raise BadValue(u"You must include your message after the %(key)s " \
                            "keyword." % {'key': NOTICE_KEYWORD.upper()})

        notice = Notice(reporter=reporter, location=role.location, \
                        text=' '.join(params))
        notice.save()

        message.respond(u"Your notice has been received. You should receive " \
                         "a response within 48 hours.")
