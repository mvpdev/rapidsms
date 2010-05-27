#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from datetime import datetime, timedelta, date

from django_tracking.models import TrackedItem

from findtb.models import *
from findtb.libs.utils import registered, generate_tracking_tag
from findtb.exceptions import ParseError, NotAllowed, BadValue


TSRS_KEYWORD = 'tsrs'
SEND_KEYWORD = 'send'
PENDING_KEYWORD = 'pending'
VOID_KEYWORD = 'void'

KEYWORDS = [
    TSRS_KEYWORD,
    SEND_KEYWORD,
    PENDING_KEYWORD,
    VOID_KEYWORD,
]


@registered
def handle(keyword, params, message):

    # verify that the message.reporter has a Role object with the lab tech
    # group and the current location
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

    # Create a mapping of keywords to handler functions
    function_mapping = {
        TSRS_KEYWORD: tsrs,
        SEND_KEYWORD: send,
        PENDING_KEYWORD: pending,
        VOID_KEYWORD: void,
    }

    # Call the appropriate handler function
    function_mapping[keyword](params, location, reporter, message)

def tsrs(params, location, reporter, message):

    if len(params) == 0:
        raise ParseError("Specimen sample registration failed. " \
                         "You must send the registration number")

    text = ' '.join(params)

    #Reject if there are multiple patient IDs
    match = re.match(r'^(\d+[ -./\\_]+\d{2}(\s+|$)){2,}' \
                      '(\+\s?n(ote)?\s*(?P<note>.*))?$', text)
    if match:
        raise BadValue("FAILED: You can only register one specimen at a " \
                       "time. Please send a separate TSRS SMS for each " \
                       "patient.")


    this_year = date.today().strftime("%y")
    last_year = (date.today() - timedelta(weeks=52)).strftime("%y")
    regex = r'^(?P<patient>\d+)[ -./\\_]+(?P<year>(%(this)s|%(last)s))' \
             '\s*(\+\s?n(ote)?\s*(?P<note>.*))?$' % \
                      {'this':this_year, 'last':last_year}

    match = re.match(regex, text)
    if not match:
        raise ParseError("FAILED: Invalid patient registration number. " \
                         "Should be in the " \
                         "format XXXX/YY where XXXX is a number and YY " \
                         "is the last two digits of year when specimen " \
                         "was registered.")


    id_first = int(match.groupdict()['patient'])
    id_years = match.groupdict()['year']

    registration_number =  '%d/%s' % (id_first, id_years)

    # Check for existing patient with same id at the location
    try:
        patient = Patient.objects.get(registration_number=registration_number,
                                         location=location)

    except Patient.DoesNotExist:
        patient = Patient()
        patient.created_by = message.reporter
        patient.location = location
        patient.registration_number = registration_number
        patient.save()

    #Don't let them send multiple samples for the same patient within 12 hours
    for state in list(SpecimenRegistered.objects.get_current_states()) + \
                 list(SpecimenSent.objects.get_current_states()):
        if state.content_object.specimen.patient == patient and \
           state.created > (datetime.now() - timedelta(hours=12)):
            raise NotAllowed("You have already registered a specimen for " \
                             "patient %(patient)s today. You cannot " \
                             "register more than one specimen for the same " \
                             "patient in a day." % {'patient':patient})

    # is if this specimen is a replacement for a previous invalidated specimen?
    try:
        previous_specimen = patient.specimen_set.all().order_by('-created_on')[0]
    except IndexError:
        is_renew = False
    else:
        ti, created = TrackedItem.get_tracker_or_create(previous_specimen)
        is_renew = isinstance(ti.state.content_object, SpecimenMustBeReplaced)

    specimen = Specimen()
    if not Specimen.objects.count():
        specimen.tracking_tag = generate_tracking_tag()
    else:
        last_tag = Specimen.objects.all().order_by('-id')[0].tracking_tag
        specimen.tracking_tag = generate_tracking_tag(last_tag)

    specimen.created_by = message.reporter
    specimen.patient = patient
    specimen.location = location
    specimen.save()

    if is_renew:
        ti.state.content_object.next_specimen = specimen
        ti.state.content_object.save()




    note = match.groupdict()['note'] or ''
    state = SpecimenRegistered(specimen=specimen, note=note)
    state.save()
    TrackedItem.add_state_to_item(specimen, state)

    message.respond("SUCCESS " \
                    "for patient %(patient)s. Tracking tag is " \
                    "%(tag)s. You must write this tag down as you will " \
                    "need it when you send the SEND message." % \
                    {'patient':patient.zero_id(), \
                     'tag':specimen.tracking_tag}, 'success')


def send(params, location, reporter, message):
    """
    Handler for the 'SEND' keyword
    """
    PARSE_ERROR_MSG = "Sending FAILED. You must indicate the method of " \
                      "specimen transport " \
                      "(POST, ZTLS or OTHER) followed by the specimen " \
                      "tracking tag(s)"

    # Check if there are any specimens to be sent for this location
    pending = False
    for spec in SpecimenRegistered.objects.get_specimens():
        if spec.location == location:
            pending = True
            break
    if not pending:
        message.respond("DTU %(dtu)s has no pending specimens to be sent. " \
                        "Send TSRS if you need to register a new sample." % \
                        {'dtu':location})
        return
    if len(params) < 2:
        raise ParseError(PARSE_ERROR_MSG)

    # If the first param is not POST, ZTLS, or OTHER, reject it.
    if params[0] not in dict(SpecimenSent.SENDING_METHOD_CHOICES).keys():
        raise ParseError(PARSE_ERROR_MSG)

    sending_method = params.pop(0)

    text = ' '.join(params)
    match = re.match(r'(?P<tags>.*?)(\+\s?n(ote)?\s*(?P<note>.*))?$', text)
    if not match or not match.groupdict()['tags']:
        raise ParseError(PARSE_ERROR_MSG)
    note = match.groupdict()['note'] or ''

    # If the sending method is other, they must specify the method used
    # in the note, so reject if they don't.
    if sending_method == 'other' and not note:
        raise ParseError("Sending FAILED. If method of transport is OTHER " \
                         "you MUST send a note (by sending +N) explaining " \
                         "the method of transport. Please send again.")

    tags = []
    for tag in re.split(r'[ .,]', match.groupdict()['tags']):
        if not tag:
            continue
        tags.append(tag)
    if not tags:
        raise ParseError("FAILED. You must send the tracking tags of the " \
                         "specimens. Send PENDING to lookup tracking tags.")


    # Create a list of the pending specimens' tracking tags for this location
    pending_tags = []
    for spec in SpecimenRegistered.objects.get_specimens():
        if spec.location == location:
            pending_tags.append(spec.tracking_tag.lower())

    # Check if the tags are valid, pending tags.
    samples = []
    bad_tags = []
    for tag in set(tags):
        if tag in pending_tags:
            samples.append(Specimen.objects.get(tracking_tag__iexact=tag))
        else:
            bad_tags.append(tag.upper())

    if len(bad_tags) == 1:
        bad_string = u"%s is not a valid current tracking tag." % bad_tags[0]

    elif len(bad_tags) > 1:
        tags_string = ', '.join(bad_tags[:-1]) + ' and ' + bad_tags[-1]
        bad_string = "%(tags)s are not valid tracking " \
                     "tags." % {'tags':tags_string}

    if len(bad_tags) == 1 and len(samples) == 0:
        raise BadValue("Sending failed. %s Please check and try again. " \
                       "You can use PENDING to " \
                       "lookup valid tracking tags." % bad_string)
    elif len(bad_tags) > 0:
        raise BadValue("Sending failed. %s No specimens sent. " \
                       "You must send all tags " \
                       "again. Use PENDING to " \
                       "lookup valid tracking tags." % bad_string)

    # Set the state for all of the specimens
    for specimen in samples:
        state = SpecimenSent(specimen=specimen, note=note, \
                             sending_method=sending_method)
        state.save()
        TrackedItem.add_state_to_item(specimen, state)

    num = len(samples)
    if num == 1:
        text = "Specimen for patient"
    else:
        text = "%(num)s specimens for patients" % {'num':num}

    patients = [t.patient.zero_id() for t in samples]

    if num == 1:
        patient_string = patients[0]
    else:
        patient_string = ', '.join(patients[:-1]) + ' and ' + patients[-1]

    #TODO notify others
    message.respond("SUCCESS: %(text)s %(patient)s " \
                    " sent through %(method)s." % \
                    {'text':text, 'patient':patient_string, \
                     'method':sending_method.upper()}, 'success')

def pending(params, location, reporter, message):
    """
    Send the reporter a list of all the specimens in the state of
    SpecimenRegistered for their location.
    """
    infos = []
    for spec in SpecimenRegistered.objects.get_specimens():
        if spec.location == location:
            infos.append("Tag %s for patient %s" % (spec.tracking_tag, \
                                                    spec.patient))
    if not infos:
        message.respond("There are no specimens pending to be sent for DTU " \
                        "%(location)s." % {'location':location})
        return
    else:
        if len(infos) == 1:
            info_string = infos[0]
        else:
            info_string = ', '.join(infos[:-1]) + ' and ' + infos[-1]
        message.respond("Pending specimens to be sent from %(dtu)s: " \
                        "%(info)s" % {'dtu':location, 'info':info_string})

def void(params, location, reporter, message):
    """
    Void specimens that have been registered, but not sent. Params should be
    tracking tags.
    """

    # Check if there are any specimens to be sent for this location
    pending = False
    for spec in SpecimenRegistered.objects.get_specimens():
        if spec.location == location:
            pending = True
            break
    if not pending:
        message.respond("DTU %(dtu)s has no pending specimens to be voided." % \
                        {'dtu':location})
    text = ' '.join(params)
    match = re.match(r'(?P<tags>.*?)(\+\s?n(ote)?\s*(?P<note>.*))?$', text)
    if not match or not match.groupdict()['tags']:
        raise ParseError("FAILED: No valid tracking tags to void.")

    note = match.groupdict()['note'] or ''

    tags = []
    for tag in re.split(r'[ .,]', match.groupdict()['tags']):
        if not tag:
            continue
        tags.append(tag)
    if not tags:
        raise ParseError("FAILED: No valid tracking tags to void.")

    # Create a list of the pending specimens' tracking tags for this location
    pending_tags = []
    for spec in SpecimenRegistered.objects.get_specimens():
        if spec.location == location:
            pending_tags.append(spec.tracking_tag.lower())

    # Check if the tags are valid, pending tags.
    samples = []
    bad_tags = []
    for tag in set(tags):
        if tag in pending_tags:
            samples.append(Specimen.objects.get(tracking_tag__iexact=tag))
        else:
            bad_tags.append(tag.upper())

    if len(bad_tags) == 1:
        bad_string = u"%s is not a valid current tracking tag." % bad_tags[0]

    elif len(bad_tags) > 1:
        tags_string = ', '.join(bad_tags[:-1]) + ' and ' + bad_tags[-1]
        bad_string = "%(tags)s are not valid tracking " \
                     "tags." % {'tags':tags_string}

    if len(bad_tags) == 1 and len(samples) == 0:
        raise BadValue("Void failed. %s Please check and try again. " \
                       "You can use PENDING to " \
                       "lookup valid tracking tags." % bad_string)
    elif len(bad_tags) > 0:
        raise BadValue("Void failed. %s No specimens voided. " \
                       "Use PENDING to " \
                       "lookup valid tracking tags." % bad_string)


    # Set the state for all of the specimens
    for specimen in samples:
        state = SpecimenInvalid(specimen=specimen, note=note, \
                                new_requested=False, cause='voided')
        state.save()
        TrackedItem.add_state_to_item(specimen, state)

    infos = []
    for spec in samples:
        infos.append("Tag %s for patient %s" % (spec.tracking_tag, \
                                                spec.patient))
    #TODO Actually void
    if len(infos) == 1:
        info_string = infos[0]
    else:
        info_string = ', '.join(infos[:-1]) + ' and ' + infos[-1]
    message.respond("Successfully voided samples: " \
                    "%(info)s" % {'info':info_string})
