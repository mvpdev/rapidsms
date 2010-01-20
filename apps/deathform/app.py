#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Deathform app

Death reporting, both for registered childcount cases and individuals
not registered
'''

import re
import time
import datetime
from functools import wraps

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from django.utils.translation import ugettext_lazy as _

from childcount.models.logs import MessageLog
from childcount.models.general import Case
from childcount.models.config import Configuration as Cfg
from deathform.models.general import ReportDeath


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

    '''Deathform main App

    general death reporting: death
    registered case/child reporting: cdeath, death
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
        Return False on error and if no function matched '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            # make sure we tell them that we got a problem
            command_list = [method for method in dir(self) \
                            if hasattr(getattr(self, method), "format")]
            input_text = message.text.lower()
            for command in command_list:
                format = getattr(self, command).format
                try:
                    first_word = (format.split(" "))[0]
                    if input_text.find(first_word) > -1:
                        message.respond(format)
                        return True
                except:
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

    def find_case(self, ref_id):
        '''Find a registered case

        return the Case object
        raise HandlerFailed if case not found
        '''
        try:
            return Case.objects.get(ref_id=int(ref_id))
        except Case.DoesNotExist:
            raise HandlerFailed(_("Case +%(ref_id)s not found.") % \
                                {'ref_id': ref_id})

    @keyword("death (\S+) (\S+) ([MF]) (\d+[YM]) (\d+) ([A-Z]) ([A-Z])?(.+)*")
    @registered
    def report_death(self, message, last, first, gender, age, dod, \
                     cause, where, description=""):
        '''reports a death

        Format: death [last_name] [first_name] [gender m/f] [age[m/y]]
        [date of death ddmmyy] [cause P/B/A/I/S] [location H/C/T/O]
        [description]
        '''
        if age[len(age) - 1].upper() == 'Y':
            age = int(age[:len(age) - 1]) * 12
        else:
            age = int(age[:len(age) - 1])

        if len(dod) != 6:
            # There have been cases where a date like 30903 have been sent and
            # when saved it gives some date that is way off
            raise HandlerFailed(_("Date must be in the format ddmmyy:"\
                                  " %(dod)s") % {'dod': dod})
        else:
            dod = re.sub(r'\D', '', dod)
            try:
                dod = time.strptime(dod, "%d%m%y")
            except ValueError:
                try:
                    dod = time.strptime(dod, "%d%m%Y")
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %(dod)s")\
                                         % {'dod': dod})
            dod = datetime.date(*dod[:3])
        if description is None:
            description = "No description"
        reporter = message.persistant_connection.reporter
        death = ReportDeath(last_name=last, first_name=first, \
                    gender=gender.upper(), \
                    age=age, reporter=reporter, where=where.upper(), \
                    cause=cause.upper(), description=description, dod=dod)
        #Perform Location checks
        if death.get_where() is None:
            raise HandlerFailed(_("Location `%(loc)s` is not known. "\
                        "Please try again with a known location") % \
                        {'loc': where})
        #Perform Cause Check
        if death.get_cause() is None:
            raise HandlerFailed(_("Cause `%(cause)s` is not known. "\
                    "Please try again with a known death cause") % \
                    {'cause': cause})

        death.save()
        info = death.get_dictionary()
        message.respond(_("%(name)s [%(age)s] died on %(dod)s of "\
                          "%(cause)s at %(where)s") % info)
        return True
    report_death.format = "death [last_name] [first_name] [gender m/f] "\
        "[age[m/y]] [date of death ddmmyy] [cause P/B/A/I/S] "\
        "[location H/C/T/O] [description]"

    keyword.prefix = ["cdeath", "death"]

    @keyword("\+(\d+) (\d+) ([A-Z]) ([A-Z])?(.+)*")
    @registered
    def report_cdeath(self, message, ref_id, dod, cause, where, \
                      description=""):
        '''records a child death, the child should be already
        registered with childcount

        Format: death [patient_ID] [date of death ddmmyy]
        [cause P/B/A/I/S] [location H/C/T/O] [description]
        '''
        #Is the child registered with us?
        case = self.find_case(ref_id)
        age = case.age()
        if age[len(age) - 1].upper() == 'Y':
            age = int(age[:len(age) - 1]) * 12
        else:
            age = int(age[:len(age) - 1])

        if len(dod) != 6:
            # There have been cases where a date like 30903 have been sent and
            # when saved it gives some date that is way off
            raise HandlerFailed(_("Date must be in the format ddmmyy:"\
                                  " %(dod)s") % {'dod': dod})
        else:
            dod = re.sub(r'\D', '', dod)
            try:
                dod = time.strptime(dod, "%d%m%y")
            except ValueError:
                try:
                    dod = time.strptime(dod, "%d%m%Y")
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %(dod)s")\
                                         % {'dod': dod})
            dod = datetime.date(*dod[:3])
        if description is None:
            description = "No description"
        reporter = message.persistant_connection.reporter
        death = ReportDeath(last_name=case.last_name.upper(), \
                            first_name=case.first_name.upper(), \
                            gender=case.gender.upper(), \
                            age=age, reporter=reporter, where=where.upper(), \
                            cause=cause.upper(), \
                            description=description, dod=dod, case=case)
        #Perform Location checks
        if death.get_where() is None:
            raise HandlerFailed(_("Location `%(loc)s` is not known. "\
                        "Please try again with a known location") % \
                        {'loc': where})
        #Perform Cause Check
        if death.get_cause() is None:
            raise HandlerFailed(_("Cause `%(cause)s` is not known. "\
                        "Please try again with a known death cause") % \
                        {'cause': cause})

        death.save()
        case.set_status(Case.STATUS_DEAD)
        case.save()
        info = death.get_dictionary()
        message.respond(_("%(name)s [%(age)s] died on %(dod)s of %(cause)s "\
                          "at %(where)s") % info)
        return True
    report_cdeath.format = "cdeath [patient_ID] [date of death ddmmyy] "\
        "[cause P/B/A/I/S] [location H/C/T/O] [description]"
