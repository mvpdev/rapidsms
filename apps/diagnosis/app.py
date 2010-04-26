#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Diagnosis App

Diagnostics
'''

import re
import datetime
from functools import wraps

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from django.db import models
from django.utils.translation import ugettext as _

from childcount.models.logs import MessageLog, log
from childcount.models.general import Case
from childcount.models.config import Configuration as Cfg
from diagnosis.models import ReportDiagnosis, Diagnosis, Lab, LabDiagnosis

find_diagnostic_re = re.compile('( -[\d\.]+)', re.I)
find_lab_re = re.compile('(/[A-Z]+)([\+-])(\d*:?)', re.I)


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

    @keyword(r'd \+(\d+ )(.*)')
    @registered
    def diagnosis(self, message, ref_id, text):
        '''Diagnosis of a case'''
        case = self.find_case(ref_id)
        reporter = message.persistant_connection.reporter
        diags = []
        labs = []

        hits = find_diagnostic_re.findall(message.text)
        for hit in hits:
            code = hit[2:]
            try:
                diags.append(Diagnosis.objects.get(code__iexact=code))
            except Diagnosis.DoesNotExist:
                raise HandlerFailed("Unknown diagnosis code: %(code)s" % \
                                    {'code': code})

        hits = find_lab_re.findall(text)
        for hit in hits:
            code, sign, number = hit
            try:
                # the code starts with /
                labs.append([Lab.objects.get(code__iexact=code[1:]), \
                             sign, number])
            except Lab.DoesNotExist:
                raise HandlerFailed("Unknown lab code: %(code)s" % \
                                    {'code': code})

        self.delete_similar(case.reportdiagnosis_set)
        report = ReportDiagnosis(case=case, reporter=reporter, \
                                 text=message.text)
        report.save()
        for diag in diags:
            report.diagnosis.add(diag)
        for lab, sign, number in labs:
            ld = LabDiagnosis()
            ld.lab = lab
            ld.result = int(sign == "+")
            if number:
                ld.amount = number
            ld.diagnosis = report
            ld.save()
        report.save()

        info = case.get_dictionary()
        info.update(report.get_dictionary())
        if info['labs_text']:
            info['labs_text'] = "%sLabs: %s" % (info['diagnosis'] and " " \
                                                or "", info['labs_text'])

        message.respond(_("D> +%(ref_id)s %(first_name_short)s.%(last_name)s "\
                          "%(diagnosis)s%(labs_text)s") % info)

        # add in the forward of instructions to the case provider
        # if that it is not the reporter of the issue

        instructions = []
        for diagnosis in report.diagnosis.all():
            if diagnosis.instructions:
                instructions.append(diagnosis.instructions)

        if instructions:
            if reporter != case.reporter:
                # there's a different provider
                info = {'ref_id': ref_id, 'instructions': \
                        (", ".join(instructions))}
                message.forward(case.reporter.connection().identity, \
                                "D> +%(ref_id)s %(instructions)s" % info)

        log(case, 'diagnosis_taken')
        return True

    def delete_similar(self, queryset):
        '''Deletes identical records'''
        try:
            last_report = queryset.latest('entered_at')
            if (datetime.datetime.now() - last_report.entered_at).days == 0:
                # last report was today. so delete it before filing another.
                last_report.delete()
        except models.ObjectDoesNotExist:
            pass
