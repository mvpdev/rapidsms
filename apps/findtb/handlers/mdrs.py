#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from datetime import datetime, date, timedelta

from findtb.models import *
from findtb.utils import registered, clean_names, generate_tracking_tag
from findtb.exceptions import ParseError, NotAllowed, BadValue

MDRS_KEYWORD = 'mdrs'
SEND_KEYWORD = 'send'
PENDING_KEYWORD = 'pending'
VOID_KEYWORD = 'void'

KEYWORDS = [
    MDRS_KEYWORD,
    SEND_KEYWORD,
    PENDING_KEYWORD,
    VOID_KEYWORD,
]


@registered
def handle(keyword, params, message):

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
        raise NotAllowed("You do not have permission to access the " \
                         "Specimen Referral system.")

    function_mapping = {
        MDRS_KEYWORD: mdrs,
        SEND_KEYWORD: send
    }
    function_mapping[keyword](params, location, reporter, message)
    
def mdrs(params, location, reporter, message):
    if len(params) == 0:
        raise ParseError("Specimen sample registration failed. " \
                         "You must send the PatientID")

    specimen = Specimen()
    if not Specimen.objects.count():
        specimen.tracking_tag = generate_tracking_tag()
    else:
        last_tag = Specimen.objects.all().order_by('-id')[0].tracking_tag
        specimen.tracking_tag = generate_tracking_tag(last_tag)
    patient = Patient()
    patient.created_by = specimen.created_by = message.reporter
    patient.location = specimen.location = location

    text = ' '.join(params)
    match = re.match(r'^(?P<patient>\d+)[ -./\\_]+(?P<year>\d{2})\s*' \
                      '(\+\s?n(ote)?\s*(?P<note>.*))?$',text)
    if not match:
        raise ParseError("FAILED: Invalid patient registration number. " \
                         "Should be in the " \
                         "format XXXX/YY where XXXX is a number and YY " \
                         "is the last two digits of year when patient " \
                         "was registered.")

    
    patient.patient_id = '%04d/%s' % \
                                (int(match.groupdict()['patient']), \
                                 match.groupdict()['year'])

    note = match.groupdict()['note'] or ''

    patient.save()
    
    specimen.patient = patient
    specimen.save()
    
    state = SpecimenRegistered(specimen=specimen, note=note)
    
    state.save()
    
    tracked_specimen, created = TrackedItem.get_tracker_or_create(specimen)
    tracked_specimen.state = state
    tracked_specimen.save()
    
    message.respond("SUCCESS " \
                    "for patient %(patient)s. Tracking tag is " \
                    "%(tag)s. You must write this tag down as you will " \
                    "need it when you send the SEND message." % \
                    {'patient':patient.patient_id, \
                     'tag':specimen.tracking_tag})


def send(params, location, reporter, message):
    #TODO pending STATE: Check if there are any in the 'pending' state, bail
    #if not
    if len(params) < 2:
        raise ParseError("Sending failed. You must send: TrackingTag " \
                         "followed by POST or ZTLS")
    text = ' '.join(params)
    match = re.match(r'(?P<tags>.*?)(\+\s?n(ote)?\s*(?P<note>.*))?$', text)
    if not match or not match.groupdict()['tags']:
        raise ParseError("FAILED. You must send the tracking tags of the " \
                         "samples. Send PENDING to lookup tracking tags.")

    if match.groupdict()['note']:
        pass
        #TODO Record note in state

    tags = []
    for tag in re.split(r'[ .,]', match.groupdict()['tags']):
        if not tag:
            continue
        tags.append(tag)
    if not tags:
        raise ParseError("FAILED. You must send the tracking tags of the " \
                         "samples. Send PENDING to lookup tracking tags.")

    samples = []
    bad_tags = []
    for tag in tags:
        #TODO only check against PENDING samples
        try:
            samples.append(Specimen.objects.get(tracking_tag__iexact=tag))
        except Specimen.DoesNotExist:
            bad_tags.append(tag)

    if len(bad_tags) == 1 and len(samples) == 0:
        raise BadValue("Sending failed. %s is not a valid tracking tag. " \
                       "Please check and try again. You can use PENDING to " \
                       "lookup valid tracking tags." % bad_tags[0])
    elif len(bad_tags) > 0:
        #TODO Fix for singular
        tags_string = ', '.join(bad_tags[:-1]) + ' and ' + bad_tags[-1]
        raise BadValue("Sending failed.  %(tags)s are not valid tracking " \
                       "tags. No samples sent. You must send all tags " \
                       "again. Use PENDING to " \
                       "lookup valid tracking tags." % {'tags':tags_string})
