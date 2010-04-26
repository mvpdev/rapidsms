#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Birth app

Records Births and then registers new case
'''

import re
import time
import datetime
from functools import wraps

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from childcount.models.logs import MessageLog, log
from childcount.models.general import Case
from childcount.models.config import Configuration as Cfg
from birth.models import ReportBirth


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this"\
                              " program.%(msg)s") % {'msg': ""})
            return True
    return wrapper


class HandlerFailed (Exception):
    pass


class App (rapidsms.app.App):

    '''Birth main app

    Records Births and then registers new case: birth
    '''

    MAX_MSG_LEN = 140
    keyword = Keyworder()
    handled = False

    def start(self):
        '''Configure your app in the start phase.'''
        pass

    def parse(self, message):
        ''' Parse incoming messages.

        flag message as not handled '''
        message.was_handled = False

    def handle(self, message):
        ''' Function selector

        Matchs functions with keyword using Keyworder
        Replies formatting advices on error
        return False on error and if no function matched '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            # make sure we tell them that we got a problem
            command_list = [method for method in dir(self) \
                            if hasattr(getattr(self, method), 'format')]
            birth_input = message.text.lower()
            for command in command_list:
                format = getattr(self, command).format
                try:
                    first_word = (format.split(' '))[0]
                    if birth_input.find(first_word) > -1:
                        message.respond(format)
                        return True
                except Exception, e:
                    pass
            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)

            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call %(mobile)s") \
                            % {'mobile': Cfg.get('developer_mobile')})
            return True
            raise
        message.was_handled = bool(self.handled)
        return self.handled

    def cleanup(self, message):
        ''' log message '''
        if bool(self.handled):
            log = MessageLog(mobile=message.peer,
                         sent_by=message.persistant_connection.reporter,
                         text=message.text,
                         was_handled=message.was_handled)
            log.save()

    def outgoing(self, message):
        '''Handle outgoing message notifications.'''
        pass

    def stop(self):
        '''Perform global app cleanup when the application is stopped.'''
        pass

    @keyword('birth (\S+) (\S+) ([MF]) (\d+) ([0-9]*\.[0-9]+|[0-9]+)' \
             ' ([A-Z]) (\S+)?(.+)*')
    @keyword('birth (\S+) (\S+) ([MF]) (\d+) ([0-9]*\.[0-9]+|[0-9]+)kg' \
             ' ([A-Z]) (\S+)?(.+)*')
    @registered
    @transaction.commit_on_success
    def report_birth(self, message, last, first, gender, dob, weight, where, \
                      guardian, complications=''):
        '''Record births and register the child as a new case

        format: birth [last name] [first name] [gender m/f]
             [dob ddmmyy] [weight in kg] location[H/C/T/O] [guardian]
             (complications)
        response: a case reference no. for the new born
        '''
        if len(dob) != 6:
            # There have been cases where a date like 30903 have been sent and
            # when saved it gives some date that is way off
            raise HandlerFailed(_("Date format is ddmmyy: %(dob)s")\
                                 % {'dob': dob})
        else:
            dob = re.sub(r'\D', '', dob)
            try:
                dob = time.strptime(dob, "%d%m%y")
            except ValueError:
                try:
                    dob = time.strptime(dob, "%d%m%Y")
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %(dob)s")\
                                         % {'dob': dob})
            dob = datetime.date(*dob[:3])
        reporter = message.persistant_connection.reporter
        location = None
        if not location:
            if reporter.location:
                location = reporter.location

        info = {
            'first_name': first.title(),
            'last_name': last.title(),
            'gender': gender.upper(),
            'dob': dob,
            'guardian': guardian.title(),
            'mobile': '',
            'reporter': reporter,
            'location': location}

        abirth = ReportBirth(where=where.upper())
        #Perform Location checks
        if abirth.get_where() is None:
            raise HandlerFailed(_("Location `%(location)s` is not known. " \
                "Please try again with a known location")\
                 % {'location': where})

        iscase = Case.objects.filter(first_name=info['first_name'], \
                        last_name=info['last_name'], \
                        reporter=info['reporter'], dob=info['dob'])
        if iscase:
            info['PID'] = iscase[0].ref_id

            # TODO: log this message
            case = iscase[0]
        else:
            case = Case(**info)
            case.save()
            log(case, 'patient_created')

        info.update({
            'id': case.ref_id,
            'last_name': last.upper(),
            'age': case.age(),
            'dob': dob.strftime("%d/%m/%y")})

        info2 = {
            'case': case,
            'weight': weight,
            'where': where,
            'reporter': reporter,
            'complications': complications}

        #check if birth has already been reported
        rbirth = ReportBirth.objects.filter(case=case)

        if rbirth:
            raise HandlerFailed(_("The birth of %(last_name)s, "\
                                  "%(first_name)s (+%(PID)s) " \
                "has already been reported by %(reporter)s.") \
                % info)

        abirth = ReportBirth(**info2)
        abirth.save()

        info.update({'where': abirth.get_where()})

        message.respond(_(
            "Birth +%(id)s: %(last_name)s,"\
            " %(first_name)s %(gender)s/%(dob)s "\
            "(%(guardian)s) %(location)s at %(where)s") % info)

        return True
    report_birth.format = "birth [last name] [first name] [gender m/f]" \
            " [dob ddmmyy] [weight in kg] location[H/C/T/O] [guardian]" \
            " (complications)"
