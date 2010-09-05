#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import itertools
import urllib2
from functools import wraps
from urllib import urlencode

from django.utils.datastructures import SortedDict

import rapidsms
from rapidsms.webui import settings

from findtb.exceptions import NotRegistered
from findtb.models.models import FINDTBGroup, Role, FINDTBLocation
from findtb import config
from format_timedelta import humanize_timedelta

from django_tracking.models import State

# TODO: move the send_msg stuff to reporters and locations sublasses

def send_msg(reporter, text):
    '''
    Sends a message to a reporter using the ajax app.  This goes to
    ajax_POST_send_message in findtb app.py
    '''
    conf = settings.RAPIDSMS_APPS['ajax']
    url = "http://%s:%s/findtb/send_message" % (conf["host"], conf["port"])

    data = {'reporter': reporter.pk, \
            'text': text}
    req = urllib2.Request(url, urlencode(data))
    stream = urllib2.urlopen(req)
    stream.close()

def send_to_group_at_location(group_name, location, msg):
    for role in Role.objects.filter(group__name=group_name, location=location):
        send_msg(role.reporter, msg)

def send_to_lab_techs(location, msg):
    send_to_group_at_location(FINDTBGroup.DTU_LAB_TECH_GROUP_NAME,
                              location, msg)

def send_to_dtu_focal_person(location, msg):
    send_to_group_at_location(FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME,
                              location, msg)

def send_to_first_control_focal_person(location, msg):
    send_to_group_at_location(FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME,
                              location, msg)

def send_to_dtu(location, msg):
    send_to_lab_techs(location, msg)
    send_to_group_at_location(FINDTBGroup.CLINICIAN_GROUP_NAME, location, msg)

def send_to_ztls(location, msg):
    zone = FINDTBLocation.objects.get(pk=location.pk).get_zone()
    send_to_group_at_location(FINDTBGroup.ZONAL_TB_SUPERVISOR_GROUP_NAME,
                              zone, msg)

def send_to_dtls(location, msg):
    district = FINDTBLocation.objects.get(pk=location.pk).get_district()
    send_to_group_at_location(FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME, \
                              district, msg)
                              
def send_to_first_controller(dtu, msg):
    send_to_group_at_location(FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME, \
                              dtu, msg)

def dtls_is_lab_tech_at(location):
    find_location = FINDTBLocation.objects.get(pk=location.pk)
    return find_location.get_dtls() in find_location.get_lab_techs()

def clean_msg(text):

    '''
    Cleans the message.  It does the following:
        - Change a message of only whitespace to ''
        - Make entire message lower-case
        - Change any series of spaces greater than 1 to just one space.
        - Strip leading and trailing whitespace
    '''
    # If the message is only white space, return an empty string
    if re.match(r'^\s*$', text):
        return ''

    # make lower case, strip, and remove duplicate spaces
    return re.sub(r'\s{2,}', ' ', text.strip().lower())

def clean_names(flat_name, surname_first=True):

    '''
    Takes a persons name as a single string and returns surname,
    first names, and alias
        >>> clean_names("smith john")
        (u'Smith', u'John', u'jsmith')

    Also can be passed an optional argument surname_first=False:
        >>> clean_names("john ADAM smith", surname_first=False)
        (u'Smith', u'John Adam', u'jasmith')
    '''

    if not isinstance(flat_name, unicode):
        flat_name = unicode(flat_name)

    # Replace all occurances of 0 with o
    flat_name = re.sub('0', 'o', flat_name)

    # Replace all non-alphanumeric character with spaces
    flat_name = re.sub('\W_', ' ', flat_name)

    # Remove numbers
    flat_name = re.sub('\d', '', flat_name)

    # break up the name into a list
    names = re.findall('\w+', flat_name)

    surname = firstnames = alias = u''

    if names:
        pop_index = 0 if surname_first else -1
        surname = names.pop(pop_index).title()
        firstnames = ' '.join(names).title()
        alias = ''.join([c[0] for c in names] + [surname]).lower()

        if not names and not surname_first:
            surname, firstnames = firstnames, surname

    return surname, firstnames, alias

def respond_exceptions(func):

    '''
    A decorator that catches exceptions and sends the text of the exception
    to the sender by responding to the message object.  It can be used
    on the rapidsms.app.App methods that are passed (self, message)
    '''

    @wraps(func)
    def wrapper(self, *args):
        if len(args) == 0 or \
           not isinstance(args[0], rapidsms.message.Message):
            return func(self, *args)

        message = args[0]
        try:
            return func(self, *args)
        except Exception, e:
            message.respond(("An error has occured (%(e)s).") % \
                           {'e': e}, 'error')
            raise
    return wrapper

def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if sender property is set on message, and whether the parent
    user model is_active

    return function or raise exception '''

    @wraps(func)
    def wrapper(keyword, params, message):
        if message.persistant_connection.reporter and \
           message.persistant_connection.reporter.user_ptr.is_active:
            return func(keyword, params, message)
        else:
            raise NotRegistered
    return wrapper


def generate_tracking_tag(start=None):
    """
        Generate a unique tag. The format is xyz[...] with x, y and z picked
        from an iterable giving a new set of ordered caracters at each
        call to next. You must pass the previous tag and a patter the tag
        should validate against.

        e.g:

        >>> generate_tracking_tag()
        '3a2'
        >>> generate_tracking_tag('3a2')
        '4a2'
        >>> generate_tracking_tag('9y9')
        '2a2a'
        >>> generate_tracking_tag('2a2a')
        '3a2a'
        >>> generate_tracking_tag('9a2a')
        '2c2a'

    """
    BASE_NUMBERS='2345679'
    BASE_LETTERS='acdefghjklmnprtuvwxy'.upper()
    if start == None:
        start = '2A2'

    next_tag = []

    matrix_generator = itertools.cycle((BASE_NUMBERS,BASE_LETTERS))

    for index, c in enumerate(start):

        matrix = matrix_generator.next()
        i = matrix.index(c)
        try:
            next_char = matrix[i+1]
            next_tag.append(next_char)
            try:
                next_tag.extend(start[index+1:])
                break
            except IndexError:
                pass
        except IndexError:
            next_tag.append(matrix[0])
            try:
                start[index+1]
            except IndexError:
                matrix = matrix_generator.next()
                next_tag.append(matrix[0])
                break

    return ''.join(next_tag)


def get_specimen_by_status():
    """
    Return a dictionary of specimen by status. Example: every incoming
    specimen, every specimen waiting for a microscopy.
    Incomming specimen get a special formating.
    """

    specimens = SortedDict((('Incoming', []),
                          ('Microscopy', []),
                          ('LPA', []),
                          ('LJ', []),
                          ('MGIT', []),
                          ('SIRE(Z)', [])))

    name_and_cat = {  'SrefRegisteredReceived': 'Incoming',
                      'SrefLostOrReceived': 'Incoming',
                      'MicroscopyForm': 'Microscopy',
                      'LpaForm': 'LPA',
                      'LjForm': 'LJ',
                      'MgitForm': 'MGIT',
                      'SireForm': 'SIRE(Z)',
                      'SirezForm': 'SIRE(Z)'}

    # sent are put on top of registered incomming specimens
    sent = []
    registered = []

    for state in State.objects.filter(is_current=True).order_by('pk'):

        try: # if webform is None
            web_form = state.content_object.get_web_form().__name__
        except AttributeError:
            pass
        else:
            specimen = state.tracked_item.content_object
            specimen.delay = humanize_timedelta(state.created, suffix="") or 'N/A'

            if 'Received' in web_form:
                if not 'Registered' in web_form:
                    registered.append(specimen)
                else:
                    specimen.delay = 'N/A'
                    sent.append(specimen)
            else:
                specimens[name_and_cat[web_form]].append(state.tracked_item.content_object)

    specimens['Incoming'].extend(registered + sent)

    return specimens


