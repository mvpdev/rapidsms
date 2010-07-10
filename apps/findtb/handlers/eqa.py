#!/usr/bin/env python


import re

from django.db import IntegrityError

from django_tracking.models import TrackedItem

from locations.models import Location

from findtb.models import *
from findtb.libs.utils import registered, send_msg, \
                              send_to_dtls, send_to_dtu_focal_person, \
                              send_to_ztls, send_to_first_control_focal_person
from findtb.exceptions import ParseError, NotAllowed, BadValue

# TODO : lot of duplicate code here, refactor
# TODO : two many lines of code here, split in several files

START_KEYWORD = 'start'
COLLECT_KEYWORD = 'collect'
READY_KEYWORD = 'ready'
RECEIVE_KEYWORD = 'receive'

KEYWORDS = [
    START_KEYWORD,
    COLLECT_KEYWORD,
    RECEIVE_KEYWORD,
    READY_KEYWORD
]


@registered
def handle(keyword, params, message):

    reporter = message.persistant_connection.reporter
    # Map keyword to handler function
    {
        START_KEYWORD: start,
        COLLECT_KEYWORD: collect,
        READY_KEYWORD: ready,
        RECEIVE_KEYWORD: receive,
    }[keyword](params, reporter, message)



def start(params, reporter, message):
    """

    /!\ This function is not going to be used in production. We let it
    here because it's handy for testing and harmless. This do what the
    previous 'ready' did, but it should no in the training documentation.

    Call back function called when a DTU notifies the system that slides
    are ready for collection.
    """
    if reporter.groups.filter(name=FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME).count():

        if len(params) > 0:
            raise ParseError(u'FAILED: The "START" keyword should '\
                             u'be sent without anything else')

        role = reporter.role_set.get(group__name=FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME)
        dtu, district = role.location, role.location.parent

        # DTLS must exists
        try:
            dtls = Role.objects.get(group__name=FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME,
                                    location=district)
        except Role.DoesNotExist:
            raise NotAllowed(u"FAILED: No DTLS is registered for your district."
                             u"Please contact your DTLS so he registers with "\
                             u"the system.")

        try:
            sb = SlidesBatch(location=dtu, created_by=reporter)
            sb.save()
        # one slides batch by quarter and dtu
        except IntegrityError:
            raise NotAllowed(u"FAILED: you already started EQA for this "\
                             u"quarter in this DTU.")

        state = EqaStarts(slides_batch=sb)
        state.save()
        TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: Your DTLS is being notified that slides are ready.")

        send_to_dtls(district, 
                     u"Slides from %s are ready to be picked up for EQA" % dtu.name)

    else:
         raise NotAllowed(u"You are not allowed to use the 'START' keyword. Only "\
                          u"EQA DTU Focal Persons are.")


def collect(params, reporter, message):
    """
    Triggered when DTLS comes to pick up slides.
    """

    if reporter.groups.filter(name=FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME).count():
    
        format_error = u"Collection failed: you must send: "\
                       u"'COLLECT DTU DTUCode NumberOfSlides' or "\
                       u"'COLLECT first DTUCode1' or 'COLLECT first all'"

        if not params:
            raise ParseError(format_error)

        collect_from = params.pop(0)
    
        if collect_from == 'dtu':
        
            # syntax check for the sms
            l = len(params)
            text = ' '.join(params)
            
            if l < 2:
                raise ParseError(format_error)
            elif l == 2:
                regex = r'(?P<prefix>[0-9\-,./]+)\s+(?P<number>\d+)'
            else:
                regex = r'(?P<prefix>\d+)[ \-,./]+(?P<suffix>\d+)\s+(?P<number>\d+)'

            match = re.match(regex, text)
            if not match:
                raise ParseError(format_error)

            groupdict = match.groupdict()

            # check if the location code exists
            if groupdict.get('suffix', None) is not None:
                try:
                    code = '-'.join((groupdict['prefix'], groupdict.get('suffix', '')))
                    location = Location.objects.get(code__iexact=code)
                except Location.DoesNotExist:
                    raise BadValue(u"Collection failed: %(code)s is not a " \
                                   u"valid location code. Please correct and " \
                                   u"send again." % \
                                   {'code': code})
            else:
                code = groupdict['prefix']
                try:
                    location = Location.objects.get(code__iexact=code)
                except Location.DoesNotExist:
                    raise BadValue(u"Collection failed: %(code)s is not a " \
                                   u"valid location code. Please correct and " \
                                   u"send again." % \
                                   {'code':code})

            # location must be a dtu
            if location.type.name != 'dtu':
                raise BadValue(u"Collection failed: %s is not a DTU" % location.name)

            # there must be a first controller for the dtu
            if not Role.objects.filter(location=location,
                                       group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME).count():
                raise NotAllowed(u"Collection failed: there are no registered "\
                                 u"First Controller for this DTU. "\
                                 u"Please contact the First Controller and ask them to register with the system.")
                                 
            # dtu must be in the district of the dtls
            if not Role.objects.filter(location=location.parent,
                                       group__name=FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME,
                                       reporter=reporter).count():
                raise NotAllowed(u"Collection failed: the district of this DTU "\
                                 u"is %s(expected_district), and yours is "\
                                 u"%(dtls_district)s. You"\
                                 u"can't collect slides outside of your district." % {
                                 'expected_district': location.parent.name,
                                 'dtls_district': reporter.role_set.get(group__name=FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME).location.name
                                 })

            number = int(groupdict['number'])
            if 20 < number or number < 1:
                raise BadValue(u"Collection failed: You must collect between 1 "\
                               u"and 20 slides. You entered %s." % number)

            # slides batch must exists to be collected
            try:
                sb = SlidesBatch.objects.get_for_quarter(location)
            except SlidesBatch.DoesNotExist:
                raise NotAllowed(u"Collection failed: The system didn't start "\
                               u"EQA automatically. Ask the DTU Focal Person "\
                               u"to send the 'START' keyword.")

            # slides batch must be in ready state
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title != 'eqa_starts':
                raise NotAllowed(u"Collection failed: slides from %s have already "\
                               u"been collected" % location.name)

            # set batch in state "collected_from_dtu"

            state = CollectedFromDtu(slides_batch=sb)
            state.save()
            TrackedItem.add_state_to_item(sb, state)

            # create slides and attache to batch
            for i in range(number):
                Slide(batch=sb).save()

            message.respond(u"SUCCESS: %(number)s slide(s) from %(dtu)s "\
                            u"have been registered as collected for EQA." % {
                            'dtu': location.name,
                            'number': number })

            send_to_first_control_focal_person(location,
                                               u"Slides from %(dtu)s have been collected by DTLS." % {
                                               'dtu': location.name })
             
            send_to_dtu_focal_person(location,
                     u"DTLS has reported picking up %(number)s slides from your "\
                     u"DTU for EQA." % {'number': number })

        elif collect_from == 'first':

            # syntax check for the sms
            text = ' '.join(params)
            regex = r'''
                      ^(\d+(?:[\-,./]+\d+)*)           # first dtu code
                      (?:$|(?:\s+(\d+[\-,./]+\d+))*)$  # following dtu codes if any
                     '''

            # check syntax
            if not re.match(regex, text, re.VERBOSE):
                raise ParseError(format_error)

            # extract codes
            codes = re.findall(r'\D*(\d+(?:[\-,./]+\d+)*)\D*', text)
   
            # check if codes are dtus codes
            dtus = []
            not_dtus = []
            for code in codes:
                try:
                    dtus.append(Location.objects.get(type__name=u'dtu',
                                                     code=code))
                except Location.DoesNotExist:
                    not_dtus.append(code)
                    
            if not_dtus:
                if len(not_dtus) > 1:
                    msg = u"Collection failed: %(codes)s are not " \
                               u"valid DTU codes. Please correct and " \
                               u"send again."
                else:
                    msg = u"Collection failed: %(codes)s is not a " \
                           u"valid DTU code. Please correct and " \
                           u"send again."
                raise BadValue(msg % {'codes': ', '.join(not_dtus)})
           
            # check that codes all belong to the same first controller
            first_ctrl = Role.objects.get(location=dtus[0],
                                              group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME).reporter
            for dtu in dtus[1:]:
            
                second_ctrl = Role.objects.get(location=dtus[0],
                                              group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME).reporter
                                              
                if first_reporter != second_reporter:
                    raise NotAllowed(u"Collection failed. You tried to collect "\
                                     u" slides from different first controllers:"\
                                     u"%(first_ctrl)s for DTU %(dtu1)s and "\
                                     u"%(second_ctrl)s for DTU %(dtu2)s" % {
                                     'first_ctrl': first_ctrl,
                                     'second_ctrl': second_ctrl,
                                     'dtu1': dtus[0].name,
                                     'dtu2': dtu
                                     })
                                              
            # check that these slides are meant to leave first control
            accepted_batches = []
            rejected_batches = []

            for dtu in dtus:
                sb = SlidesBatch.objects.get_for_quarter(dtu)
                ti, c = TrackedItem.get_tracker_or_create(sb)
                if ti.state.title != 'passed_first_control':
                    rejected_batches.append(sb.location.name)
                else:
                    accepted_batches.append(sb)

            if rejected_batches:
                raise BadValue(u"Collection failed: Slides from %(codes)s have " \
                               u"not recently passed first control. Check they have " \
                               u"been tested and haven't been picked up already." % {
                               'codes': ', '.join(rejected_batches)})


            # set states
            codes = ', '.join(sb.location.code for sb in accepted_batches)
            for sb in accepted_batches:
                state = CollectedFromFirstController(slides_batch=sb)
                state.save()
                TrackedItem.add_state_to_item(sb, state)

            message.respond(u"SUCCESS: You collected slides of %(codes)s from the first controller"  % {
                            'codes': codes})

            first_control_focal_person = Role.objects.get(location=dtus[0],
                                                          group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME
                                                          ).reporter

            send_msg(first_control_focal_person,
                     u"DTLS has reported picking up slides from %(codes)s "\
                     u"from you." % {'codes': codes })


    else:
         raise NotAllowed(u"You are not allowed to use this keyword. It is "\
                          u"only for the DTLS.")


def receive(params, reporter, message):
    """
    Triggered when First Controllers notify they received slides
    """

    if reporter.groups.filter(name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME).count():

        format_error = u"Reception failed: you must send: "\
                       u"'RECEIVE DTUCode' or 'RECEIVE all'. You can "\
                       u"send several codes at the same time: "\
                       u"'RECEIVE DTUCode1 DTUCode2'."

        # syntax check for the sms
        text = ' '.join(params)
        regex = r'''
                 (?:
                  ^(\d+[\-,./]+\d+)                # first dtu code
                  (?:$|(?:\s+(\d+[\-,./]+\d+))*)$  # following dtu codes if any
                 ) | all                           # or 'all' keyword
                 '''

        # check syntax
        if not re.match(regex, text, re.VERBOSE):
            raise ParseError(format_error)

        # extract codes
        codes = re.findall(r'\D*(\d+[\-,./]+\d+|all)\D*', text)

        # if 'all', receive every collected slides
        if codes[0] == 'all':
            roles = reporter.role_set.filter(group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME)
            dtus = [role.location for role in roles]
            accepted_batches = []
            for dtu in dtus:
                try:
                    sb = SlidesBatch.objects.get_for_quarter(dtu)
                except SlidesBatch.DoesNotExist:
                    pass
                else:
                    ti, c = TrackedItem.get_tracker_or_create(sb)
                    if ti.state.title == 'collected_from_dtu':
                        accepted_batches.append(sb)

            if not accepted_batches:
                raise BadValue(u"No slides are on their way to the first controller "\
                               u"in your district")

        # check is codes are valid and for a DTU
        else:
        
            dtus = []
            not_dtus = []
            not_for_this_controller = []
            for code in codes:
                try:
                    dtu = Location.objects.get(type__name=u'dtu', code=code)
                except Location.DoesNotExist:
                    not_dtus.append(dtu)
                else:
                    try:
                        reporter.role_set.get(group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME,
                                              location=dtu)
                    except Role.DoesNotExist:
                        not_for_this_controller.append(dtu)
                    else:
                        dtus.append(dtu)
                    
            if not_dtus:
            
                if len(not_dtus) > 1:
                    msg = u"Reception failed: %(dtus)s are not " \
                               u"valid DTU codes. Please correct and " \
                               u"send again."
                else:
                    msg = u"Reception failed: %(dtus)s is not a " \
                           u"valid DTU code. Please correct and " \
                           u"send again."
                           
                raise BadValue(msg % {'dtus': ', '.join(not_dtus)})
                
                
            if not_for_this_controller:
            
                if len(not_for_this_controller) > 1:
                    msg = u"Reception failed: You are not the First Controller "\
                          u" for %(dtus)s. You can't receive their slides."
                else:
                    msg = u"Reception failed: You are not the First Controller "\
                          u" for %(dtus)s. You can't receive its slides."
                           
                raise BadValue(msg % {'dtus': 
                                      ', '.join(dtu.name for dtu in not_for_this_controller)})                

            # check that these slides are meant to go to first control
            accepted_batches = []
            rejected_batches = []

            for dtu in dtus:
                sb = SlidesBatch.objects.get_for_quarter(dtu)
                ti, c = TrackedItem.get_tracker_or_create(sb)
                if ti.state.title != 'collected_from_dtu':
                    rejected_batches.append(sb.location.name)
                else:
                    accepted_batches.append(sb)

            if rejected_batches:
                raise BadValue(u"Reception failed: Slides from %(codes)s are not " \
                               u"on their way to first control. Check they have " \
                               u"been collected by DTLS and didn't pass first "\
                               u"control already." % {
                               'codes': ', '.join(rejected_batches)})

        dtus_names = ', '.join(sb.location.name for sb in accepted_batches)
        for sb in accepted_batches:
            state = DeliveredToFirstController(slides_batch=sb)
            state.save()
            TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: You have received slides from "\
                        u"%(dtus_names)s." % {
                        'dtus_names': dtus_names
                        })

        send_to_dtls(sb.location,
                     u"Slides from %(dtus_names)s have been received by the first "\
                     u"controller" % {
                        'dtus_names': dtus_names
                        })

                                     
    elif reporter.groups.filter(name=FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME).count():
    
        if params:
            raise ParseError("'RECEIVE' must be sent without anything else.")
            
        error = u"Reception failed: check that NTRL declared slides ready "\
                u"to go back to NTRL."
        
        role = Role.objects.get(reporter=reporter,
                                group__name=FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME)
        
        # slides batch must exists to be collected
        try:
            sb = SlidesBatch.objects.get_for_quarter(role.location)
        except SlidesBatch.DoesNotExist:
            raise NotAllowed(error)

        # slides batch must be in ready state
        ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
        if ti.state.title != 'ready_to_leave_ntrl':
            raise NotAllowed(error)
            
        state = ReceivedAtDtu(slides_batch=sb)
        state.save()
        TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: You have acknowledged receiving the " \
                        u"discordant slides and feedback report. Contact " \
                        u"your DTLS if you have any questions about the " \
                        u"results.")

        send_to_dtls(sb.location,
                     u"Slides from %(dtu)s have been received by DTU. "\
                     u"End of EQA for this DTU during this quarter" % {
                        'dtu': sb.location.name
                        })
            
    else:
         raise NotAllowed(u"You are not allowed to use this keyword. Only "\
                          u"First Controllers and DTU focal persons are.")


def ready(params, reporter, message):
    """
    Triggered when First Controllers notify slides have been tested
    """

    if reporter.groups.filter(name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME).count():

        format_error = u"Reception failed: you must send: "\
                       u"'READY DTUCode' or 'READY all'. You can "\
                       u"send several codes at the same time: "\
                       u"'READY DTUCode1 DTUCode2'."

        # syntax check for the sms
        text = ' '.join(params)
        regex = r'''
                 (?:
                  ^(\d+[\-,./]+\d+)                # first dtu code
                  (?:$|(?:\s+(\d+[\-,./]+\d+))*)$  # following dtu codes if any
                 ) | all                           # or 'all' keyword
                 '''

        # check syntax
        if not re.match(regex, text, re.VERBOSE):
            raise ParseError(format_error)

        # extract codes
        codes = re.findall(r'\D*(\d+[\-,./]+\d+|all)\D*', text)

        # if 'all', receive every collected slides
        if codes[0] == 'all':
           roles = Role.objects.filter(reporter=reporter,
                                      group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME)
           dtus = [role.location for role in roles]
           accepted_batches = []
           for dtu in dtus:
               try:
                   sb = SlidesBatch.objects.get_for_quarter(dtu)
               except SlidesBatch.DoesNotExist:
                   pass
               else:
                   ti, c = TrackedItem.get_tracker_or_create(sb)
                   if ti.state.title == 'delivered_to_first_controller':
                       accepted_batches.append(sb)

           if not accepted_batches:
               raise BadValue(u"No slides are waiting for you to be controlled.")


        # check if codes are valid and for a DTU
        else:
            dtus = []
            not_dtus = []
            not_for_this_controller = []
            for code in codes:
                try:
                    dtu = Location.objects.get(type__name=u'dtu', code=code)
                except Location.DoesNotExist:
                    not_dtus.append(dtu)
                else:
                    try:
                        reporter.role_set.get(group__name=FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME,
                                              location=dtu)
                    except Role.DoesNotExist:
                        not_for_this_controller.append(dtu)
                    else:
                        dtus.append(dtu)
                    
            if not_dtus:
            
                if len(not_dtus) > 1:
                    msg = u"Reception failed: %(dtus)s are not " \
                               u"valid DTU codes. Please correct and " \
                               u"send again."
                else:
                    msg = u"Reception failed: %(dtus)s is not a " \
                           u"valid DTU code. Please correct and " \
                           u"send again."
                           
                raise BadValue(msg % {'dtus': ', '.join(not_dtus)})
                
                
            if not_for_this_controller:
            
                if len(not_for_this_controller) > 1:
                    msg = u"Reception failed: You are not the First Controller "\
                          u" for %(dtus)s. You can't control their slides."
                else:
                    msg = u"Reception failed: You are not the First Controller "\
                          u" for %(dtus)s. You can't control its slides."
                           
                raise BadValue(msg % {'dtus': 
                                      ', '.join(dtu.name for dtu in not_for_this_controller)})   

            # check that these slides are meant to go to first control
            accepted_batches = []
            rejected_batches = []

            for dtu in dtus:
                sb = SlidesBatch.objects.get_for_quarter(dtu)
                ti, c = TrackedItem.get_tracker_or_create(sb)
                if ti.state.title != 'delivered_to_first_controller':
                    rejected_batches.append(sb.location.name)
                else:
                    accepted_batches.append(sb)

            if rejected_batches:
                raise BadValue(u"Reception failed: Slides from %(codes)s are not " \
                               u"waiting for first controller. Check they have " \
                               u"been delivered by DTLS and didn't pass first "\
                               u"control already." % {
                               'codes': ', '.join(rejected_batches)})

        dtus_names = ', '.join(sb.location.name for sb in accepted_batches)
        for sb in accepted_batches:
            state = PassedFirstControl(slides_batch=sb)
            state.save()
            TrackedItem.add_state_to_item(sb, state)

        message.respond(u"SUCCESS: Your DTLS has been notified to collect the "\
                        u"slides from you for second control.")

        send_to_dtls(sb.location,
                     u"Slides from %(dtus_names)s have been tested by the first "\
                     u"controller. Please collect them for second control" % {
                        'dtus_names': dtus_names})

    else:
         raise NotAllowed(u"You are not allowed to use this keyword. Only "\
                          u"first controllers are.")
