#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Immunization main app

record administered immunizations
'''

from functools import wraps

from django.db import models
from django.utils.translation import ugettext_lazy as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from childcount.models.general import Case
from childcount.models.config import Configuration as Cfg


from followup.models import ReportImmunization


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

    '''Immunization main app

    record administered immunizations
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
        '''Perform app cleanup'''
        pass

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


    keyword.prefix = ["vaccine"]

    @keyword("\+(\d+) (\S+)")
    @registered
    def report_administered_vaccine(self, message, ref_id, vaccine):
        '''Send measles summary to health facilitators
        and those who are to receive alerts
        '''
        reporter = message.persistant_connection.reporter
        case = self.find_case(ref_id)
        period = None
        if vaccine.upper() in ('BCG', 'POLIO'):
            period = '0'
        elif vaccine.upper() in ('OPV1', 'PV1'):
            period = '6w'
        elif vaccine.upper() in ('OPV2', 'PV2'):
            period = '10w'
        elif vaccine.upper() in ('OPV3', 'PV3'):
            period = '14w'
        elif vaccine.upper() in ('VITA'):
            period = '6m'
        elif vaccine.upper() in ('M'):
            period = '9m'
        self.debug(message)
        if vaccine in ReportImmunization.VACCINE_CHOICES:
            ri = ReportImmunization(case=case, period=period, \
                                    reporter=reporter)
            ri.save()
            return True
        return False
    report_administered_vaccine.format = "vaccine "
