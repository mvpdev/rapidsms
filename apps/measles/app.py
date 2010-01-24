#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Measles main app

record vaccinated cases - measles
get summarry report - msummary
'''

from functools import wraps

from django.db import models
from django.utils.translation import ugettext_lazy as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from childcount.models.logs import MessageLog
from childcount.models.general import Case
from childcount.models.reports import ReportCHWStatus
from childcount.models.config import Configuration as Cfg
from reporters.models import Reporter, ReporterGroup
from measles.models import ReportMeasles


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

    '''Measles main app

    record vaccinated cases - measles
    get summarry report - msummary
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

    @keyword(r'measles ?(.*)')
    @registered
    def measles(self, message, text):
        '''Record vaccinated cases

        format: measles [+PID] [+PID] [+PID]
        '''
        reporter = message.persistant_connection.reporter
        cases, notcases = self.str_to_cases(text)
        result = ''
        for case in cases:
            result = result + "+%s " % case.ref_id
            report = ReportMeasles(case=case, reporter=reporter, taken=True)
            report.save()
        if result != '':
            msg = _("%(result)s received measles shot." % {'result': result})
            message.respond(_("%s") % msg)
        if notcases:
            nresult = ''
            for nc in notcases:
                nresult = nresult + "%s " % nc
            msg = _("%(nresult)s not found!!" % {'nresult': nresult})
            message.respond(_("%s") % msg)
        return True
    measles.format = "measles [+PID] [+PID] [+PID]"

    def str_to_cases(self, text):
        '''Pick PIDs and return the a list of cases they represent

        @text a string containing space separeted +PID, e.g +78 +98 ..or 78 98
        @return: Case Object list, and a list of numbers that were not cases
        '''
        text = text.replace('+', '')
        cs = text.split(' ')
        cases = []
        notcases = []
        for c in cs:
            try:
                cases.append(self.find_case(c))
            except HandlerFailed:
                notcases.append(c)
        return cases, notcases

    @keyword(r'msummary')
    def measles_summary(self, message):
        '''Send measles summary to health facilitators
        and those who are to receive alerts
        '''
        header = _(u"Measles Summary by clinic:")
        result = []

        summary = ReportCHWStatus.measles_mini_summary()
        tmp = header
        for info in summary:
            if info['eligible_cases'] != 0:
                info['percentage'] = \
                    round(float(float(info['vaccinated_cases']) / \
                                float(info['eligible_cases'])) * 100, 0)
            else:
                info['percentage'] = 0
            item = u" %(clinic)s: %(vaccinated_cases)s/%(eligible_cases)s "\
                    "%(percentage)s%%," % info
            if len(tmp) + len(item) + 2 >= self.MAX_MSG_LEN:
                result.append(tmp)
                tmp = header
            tmp += item
        if tmp != header:
            result.append(tmp)
        subscribers = Reporter.objects.all()
        for text in result:
            for subscriber in subscribers:
                try:
                    if subscriber.registered_self \
                        and ReporterGroup.objects.get(title='measles_summary')\
                             in subscriber.groups.only():
                        mobile = subscriber.connection().identity
                        message.forward(mobile, _("%(msg)s") % {'msg': text})
                except:
                    '''Alert Developer

                    The group might have not been created,
                    need to alert the developer/in charge here
                    '''
                    message.forward(Cfg.get('developer_mobile'), \
                            _("The group %(group)s has not been created."\
                               % {'group': "measles_summary"}))
        return True
    measles_summary.format = "msummary"
