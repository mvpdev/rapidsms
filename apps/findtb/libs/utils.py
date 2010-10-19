#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import os
import itertools
import urllib2
from functools import wraps
from urllib import urlencode
import numpy
import xlwt
import calendar
from datetime import time, date, datetime, timedelta
from copy import deepcopy

from django.utils.datastructures import SortedDict

import rapidsms
from rapidsms.webui import settings

from locations.models import Location
from findtb.exceptions import NotRegistered
from findtb.models.models import FINDTBGroup, Role, FINDTBLocation, Specimen
from findtb import config
from format_timedelta import humanize_timedelta

from django_tracking.models import State

# TODO: move the send_msg stuff to reporters and locations sublasses

MINUTE = 60.0
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7

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

def get_tsrs_months():
    months = []

    first = Specimen.objects.all().order_by('created_on')[0].created_on
    start = datetime(year=first.year, month=first.month, day=1)
    while True:
        end = datetime(year=start.year, month=start.month, hour=23, minute=59,
                       day=calendar.monthrange(start.year, start.month)[1])
        if end > datetime.now():
            break
        months.append([start, end])
        next_month = end + timedelta(hours=1)
        start = datetime(year=next_month.year, month=next_month.month, day=1)
    return months

def get_tsrs_stats(location=None, date_start=None, date_end=None):
    states = State.objects.filter(origin='sref') \
                          .exclude(type='alert') \
                          .exclude(cancelled=True)
    if date_start and date_end:
        states = states.filter(created__gte=date_start, created__lte=date_end)

    stats = {'microscopy_positive': 0,
             'lpa_invalid': 0,
             'lpa_rif_resistant': 0,
             'lpa_rif_inh_resistant': 0,
             'mic_neg_mgit_pos': 0,
             'mgit_rif_inh_resistant': 0,
             'resistant':0}

    state_list = []
    for state in states:
        ti = state.tracked_item
        co = ti.content_object
        if location and \
            location not in co.location.ancestors(include_self=True):
            continue
        state_list.append(state)

    

    stats['microscopy_positive'] = \
        len(filter(lambda x: x.title == 'microscopy' and \
                             x.content_object.is_positive(), state_list))

    stats['lpa_invalid'] = \
        len(filter(lambda x: x.title == 'lpa' and \
                             not x.content_object.is_valid(), state_list))

    stats['lpa_rif_resistant'] = \
        len(filter(lambda x: x.title == 'lpa' and \
                             x.content_object.rif == 'resistant', state_list))
    stats['lpa_rif_inh_resistant'] = \
        len(filter(lambda x: x.title == 'lpa' and \
                             x.content_object.rif == 'resistant' and \
                             x.content_object.inh == 'resistant', state_list))

    for state in filter(lambda x: x.title == 'microscopy' and \
                                  not x.content_object.is_positive(), \
                        state_list):
        try:
            mgit = state.tracked_item.states.get(title='mgit')
        except State.DoesNotExist:
            continue
        if mgit.content_object.result == 'positive':
            stats['mic_neg_mgit_pos'] += 1


    for state in filter(lambda x: x.title == 'sent', state_list):
        try:
            lpa = state.tracked_item.states.get(title='lpa')
        except State.DoesNotExist:
            pass
        else:
            if lpa.content_object.rif == 'resistant' and \
               lpa.content_object.inh == 'resistant':
                stats['resistant'] += 1
                continue
        try:
            sirez = state.tracked_item.states.get(title='sirez')
        except State.DoesNotExist:
            pass
        else:
            if sirez.content_object.rif == 'resistant' and \
               sirez.content_object.inh == 'resistant':
                stats['resistant'] += 1


    stats['mgit_rif_inh_resistant'] = \
        len(filter(lambda x: x.title == 'sirez' and \
                             x.content_object.rif == 'resistant' and \
                             x.content_object.inh == 'resistant', state_list))

    return stats

def num_resistant(location=None, date_start=None, date_end=None):
    stats = get_stats_for_state('sref', 'sent', location=location, 
                                date_start=date_start, date_end=date_end)
    print stats
 

def get_stats_for_state(origin, state, location=None, cutoff=None,
                        date_start=None, date_end=None, num_only=False):
    states = State.objects.filter(title=state, origin=origin) \
                          .exclude(type='alert') \
                          .exclude(cancelled=True)

    items = []
    for state in states:
        ti = state.tracked_item
        co = ti.content_object
        if location and \
            location not in co.location.ancestors(include_self=True):
            continue
        if date_start and state.created < date_start:
            continue
        if date_end and state.created > date_end:
            continue
        all_states = list(ti.states.exclude(type='alert') \
                                   .exclude(cancelled=True) \
                                   .order_by('created'))
        try:
            previous_state = all_states[all_states.index(state)-1]
        except IndexError:
            continue
        items.append({'co':co,
                      'duration': state.created - previous_state.created})

    stats = {'num': len(items)}
    if len(items) == 0 or num_only:
        return stats

    items.sort(key=lambda x: x['duration'])
    stats['items'] = [item['co'] for item in items]
    stats.update({'min': items[0]['duration'], 'min_item': items[0]['co']})
    stats.update({'max': items[-1]['duration'], 'max_item': items[-1]['co']})

    durations = [item['duration'] for item in items]
    dsum = timedelta()
    for d in durations:
        dsum += d
    stats['avg'] = dsum / len(durations)

    stats['med'] = timedelta(seconds= \
            numpy.median([d.seconds + d.days * 86400 for d in durations]))

    if cutoff:
        items_before = [item['co'] for item in \
                          filter(lambda x: x['duration'] <= cutoff, items)]
        stats['items_before_cutoff'] = items_before
        stats['num_before_cutoff'] = len(items_before)

        items_after = [item['co'] for item in \
                          filter(lambda x: x['duration'] > cutoff, items)]
        stats['items_after_cutoff'] = items_after
        stats['num_after_cutoff'] = len(items_after)

    return stats
      

def report_humanize_timedelta(delta):
    seconds = delta.days * DAY + delta.seconds
    if seconds > WEEK * 6:
        return '%d weeks' % int(round(seconds / WEEK))
    if seconds > DAY * 4:
        return '%d days' % int(round(seconds / DAY))
    if seconds > HOUR * 1:
        return '%d hours' % int(round(seconds / HOUR))
    return '%d minutes' % int(round(seconds / MINUTE))

def days_from_timedelta(delta):
    return (delta.seconds + d.days * DAY) / DAY

def create_xlwt_style(size=12, bold=False):
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.height = size * 20
    font.bold = bold
    style.font = font
    return style

def create_tsrs_xls(humanize_dates=True):
    doc_header = create_xlwt_style(14, bold=True)
    month_style = create_xlwt_style(11, bold=True)
    month_style.num_format_str = 'MMM-YYYY'
    country_header = create_xlwt_style(12)
    country_footer = create_xlwt_style(12, bold=True)
    zone_header = create_xlwt_style(11)
    zone_footer = create_xlwt_style(11, bold=True)
    district_header = create_xlwt_style(10)
    district_footer = create_xlwt_style(10, bold=True)
    dtu_style = create_xlwt_style(9)
    wb = xlwt.Workbook()
    num_sheet = wb.add_sheet('Specimens Sent')
    num_sheet.row(0).height=400
    num_sheet.write_merge(0, 0, 0, 5, 'TSRS Specimens Sent', doc_header)
    for i in range(0,2):
        num_sheet.col(i).width = 600
    num_sheet.col(2).width = 6000

    col = 3
    months = get_tsrs_months()
    for month in months:
        num_sheet.write(1, col, month[0], month_style)
        col += 1
    num_sheet.write(1, col, "Total", month_style)
    col += 1
    num_sheet.write(1, col, "MDR", month_style)

    level = 0
    i = 2
    for zone in Location.objects.filter(type__name='zone'):

        num_sheet.write(i, level, "%s Zone" % zone.name, zone_header)
        num_sheet.row(i).level = level + 1
        i+=1
        level += 1
        for district in Location.objects.filter(parent=zone):
            num_sheet.write(i, level, "%s District" % district.name, district_header)
            num_sheet.row(i).level = level + 1
            i+=1
            level += 1
            for dtu in Location.objects.filter(parent=district):
                num_sheet.write(i, level, dtu.name, dtu_style)
                c = level+1
                for month in months:
                    stats = get_stats_for_state('sref','sent', location=dtu,
                                                date_start=month[0],
                                                date_end=month[1], num_only=True)
                    num_sheet.write(i, c, stats['num'], dtu_style)
                    c+=1
                stats = get_stats_for_state('sref','sent', location=dtu,
                                            date_start=months[0][0],
                                            date_end=months[-1][1], num_only=True)
                num_sheet.write(i, c, stats['num'], dtu_style)
                c+=1
                stats = get_tsrs_stats(location=dtu, date_start=months[0][0],
                                       date_end=months[-1][1])
                num_sheet.write(i, c, stats['resistant'], dtu_style)
                num_sheet.row(i).level = level
                i+=1
            level -= 1
            num_sheet.write(i, level, "%s District Total" % district.name, district_footer)
            c = level+2
            for month in months:
                stats = get_stats_for_state('sref','sent', location=district,
                                            date_start=month[0],
                                            date_end=month[1], num_only=True)
                num_sheet.write(i, c, stats['num'], district_footer)
                c+=1
            stats = get_stats_for_state('sref','sent', location=district,
                                        date_start=months[0][0],
                                        date_end=months[-1][1], num_only=True)
            num_sheet.write(i, c, stats['num'], district_footer)
            c+=1
            stats = get_tsrs_stats(location=district, date_start=months[0][0],
                                   date_end=months[-1][1])
            num_sheet.write(i, c, stats['resistant'], district_footer)
            num_sheet.row(i).level = level
            i+=1
        level -= 1
        num_sheet.write(i, level, "%s Zone Total" % zone.name, zone_footer)
        c = level+3
        for month in months:
            stats = get_stats_for_state('sref','sent', location=zone,
                                        date_start=month[0],
                                        date_end=month[1], num_only=True)
            num_sheet.write(i, c, stats['num'], zone_footer)
            c+=1
        stats = get_stats_for_state('sref','sent', location=zone,
                                    date_start=months[0][0],
                                    date_end=months[-1][1], num_only=True)
        num_sheet.write(i, c, stats['num'], zone_footer)
        c+=1
        stats = get_tsrs_stats(location=zone, date_start=months[0][0],
                               date_end=months[-1][1])
        num_sheet.write(i, c, stats['resistant'], zone_footer)
        num_sheet.row(i).level = level
        i+=1

    time_sheets = []
    for month in months:
        time_sheets.append({'start':month[0], 'end':month[1],
                           'name':month[0].strftime('%b %Y')})
    time_sheets.append({'start':months[0][0], 'end':months[-1][1],
                       'name':"Overall"})

    for time_sheet in time_sheets:
        header_style = month_style
        num_style = district_header
        percent_style = deepcopy(num_style)
        percent_style.num_format_str='0%'
        start = time_sheet['start']
        end = time_sheet['end']
        sheet = wb.add_sheet(time_sheet['name'])
        sheet.row(0).height=400
        sheet.col(0).width = 6100
        sheet.write_merge(0, 0, 0, 5, time_sheet['name'], doc_header)
        headers = ['Total', '% Within Target', 'Mean', 'Median', 'Max', 'Min']
        col = 1
        for header in headers:
            sheet.write(1, col, header, header_style)
            col += 1
        i = 2
        all_stats = []
        stat = get_stats_for_state('sref', 'received', date_start=start,
                                   date_end=end, cutoff=timedelta(hours=48))
        stat.update({'name':'Delivery'})
        all_stats.append(stat)

        stat = get_stats_for_state('sref', 'microscopy', date_start=start,
                                   date_end=end, cutoff=timedelta(hours=48))
        stat.update({'name':'Microscopy'})
        all_stats.append(stat)

        stat = get_stats_for_state('sref', 'lpa', date_start=start,
                                   date_end=end, cutoff=timedelta(days=7))
        stat.update({'name':'LPA'})
        all_stats.append(stat)

        stat = get_stats_for_state('sref', 'mgit', date_start=start,
                                   date_end=end, cutoff=timedelta(weeks=6))
        stat.update({'name':'MGIT'})

        all_stats.append(stat)
        if humanize_dates:
            date_func = report_humanize_timedelta
        else:
            date_func = days_from_timedelta
        for stat in all_stats:
            if not stat['num']:
                continue
            col = 0
            for val in [stat['name'], stat['num'],
                        stat['num_before_cutoff'] / float(stat['num']),
                        date_func(stat['avg']),
                        date_func(stat['med']), 
                        date_func(stat['max']), 
                        date_func(stat['min'])]:
                if isinstance(val, float):
                    style = percent_style
                else:
                    style = num_style
                sheet.write(i, col, val, style)
                col+=1
            i+=1
        i+=2


        other_stats = get_tsrs_stats(date_start=start, date_end=end)
        other_headers = (('Microscopy Positive', 'microscopy_positive'),
                         ('LPA Invalid', 'lpa_invalid'),
                         ('LPA RIF Resistant', 'lpa_rif_resistant'),
                         ('LPA RIF and INH Res.', 'lpa_rif_inh_resistant'),
                         ('Microscopy Neg, MGIT Pos.', 'mic_neg_mgit_pos'),
                         ('MGIT RIF and INH Res.', 'mgit_rif_inh_resistant'))

        for stat in other_headers:
            sheet.write(i, 0, stat[0], num_style)
            sheet.write(i, 1, other_stats[stat[1]], num_style)
            i+=1

    path = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                        '../static/files')

    wb.save(os.path.join(path,'TSRS Report.xls'))
