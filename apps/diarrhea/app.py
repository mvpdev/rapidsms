#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' Childcount Diarrhea App

Diarrhea Reporting Management '''

import re
import datetime

import rapidsms
from rapidsms.parsers.keyworder import Keyworder
from django.db import models
from django.utils.translation import ugettext as _

from childcount.models.general import Case
from childcount.models.logs import MessageLog, log
from childcount.models.config import Configuration as Cfg
from diarrhea.models import ReportDiarrhea, DiarrheaObservation

find_diagnostic_re = re.compile('( -[\d\.]+)', re.I)
find_lab_re = re.compile('(/[A-Z]+)([\+-])(\d*:?)', re.I)


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can " \
                            "access this program.%(msg)s") % {'msg': ''})
            return True
    return wrapper


class HandlerFailed(Exception):
    ''' No function pattern matchs message '''
    pass


class App(rapidsms.app.App):

    ''' ChildCount Diarrhea App

    Provides:
    Diarrhea reporting: ors, ors (followup) '''

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
        Replies formatting advices on error '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)

            self.handled = True
        except Exception, e:
            message.respond(_("An error occurred. Please call %(mobile)s") \
                            % {'mobile': Cfg.get('developer_mobile')})
            raise
        message.was_handled = bool(self.handled)
        return self.handled

    def cleanup(self, message):
        ''' log message if handled '''
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
        ''' Case from ID

        return Case '''

        try:
            return Case.objects.get(ref_id=int(ref_id))
        except Case.DoesNotExist:
            raise HandlerFailed(_("Case +%s not found.") % ref_id)

    # DIARRHEA
    # follow up on diarrhea

    @keyword(r'ors \+(\d+) ([yn])')
    @registered
    def followup_diarrhea(self, message, ref_id, is_ok):
        ''' Follow-up on diarrhea reporting

        Format: ors [ref_id] [is_ok - y/n]
        ref_id: case ID
        is_ok: patient new health condition

        Replies Diarrhea informations '''
        case = self.find_case(ref_id)
        is_ok = True if is_ok == "y" else False

        reporter = message.persistant_connection.reporter
        report = ReportDiarrhea.objects.get(case=case)

        if is_ok:
            report.status = ReportDiarrhea.HEALTHY_STATUS
            report.save()
        else:
            report.status = ReportDiarrhea.SEVERE_STATUS
            report.save()

            info = report.case.get_dictionary()
            info.update(report.get_dictionary())

            msg = _("%(diagnosis_msg)s. +%(ref_id)s %(last_name)s, " \
                    "%(first_name_short)s, %(gender)s/%(months)s " \
                    "(%(guardian)s). %(days)s, %(ors)s") % info
            if report.observed.all().count() > 0:
                msg += ", " + info["observed"]

            message.respond("DIARRHEA> " + msg)

        '''
        if report.status in (report.MODERATE_STATUS,
                           report.SEVERE_STATUS,
                           report.DANGER_STATUS):
            alert = _("@%(username)s reports %(msg)s") % \
                {"username":reporter.alias, "msg":msg}
            recipients = [reporter]
            for query in (Provider.objects.filter(alerts=True),
                          Provider.objects.filter(clinic=provider.clinic)):
                for recipient in query:
                    if recipient in recipients: continue
                    recipients.append(recipient)
                    message.forward(recipient.mobile, alert)
        '''
        log(case, "diarrhea_fu_taken")
        return True

    def get_diarrheaobservations(self, text):

        ''' extract obsvervations from text

        return tuple of DiarrheaObservation: (observed, all) '''
        choices = dict( \
                    [(o.letter, o) for o in DiarrheaObservation.objects.all()])
        observed = []
        if text:
            text = re.sub(r'\W+', ' ', text).lower()
            for observation in text.split(' '):
                obj = choices.get(observation, None)
                if not obj:
                    if observation != 'n':
                        raise HandlerFailed("Unknown observation code: %s" \
                                            % observation)
                else:
                    observed.append(obj)
        return observed, choices

    @keyword(r'ors \+(\d+) ([yn]) (\d+)\s?([a-z\s]*)')
    @registered
    def report_diarrhea(self, message, ref_id, ors, days, complications):
        ''' Diarrhea reporting

        Format: ors [ref_id] [ors - y/n] [days] [observations]
        ref_id: case ID
        ors: Oral Rehidratation Salt given?
        days: number of diarrhea days
        observations: codes of observations

        Replies Diarrhea informations '''
        case = self.find_case(ref_id)

        ors = True if ors == "y" else False
        days = int(days)

        observed, choices = self.get_diarrheaobservations(complications)
        self.delete_similar(case.reportdiarrhea_set)

        reporter = message.persistant_connection.reporter
        report = ReportDiarrhea(case=case, reporter=reporter, \
                                ors=ors, days=days)
        report.save()
        for obs in observed:
            report.observed.add(obs)
        report.diagnose()
        report.save()

        choice_term = dict(choices)

        info = case.get_dictionary()
        info.update(report.get_dictionary())

        msg = _("%(diagnosis_msg)s. +%(ref_id)s %(last_name)s, " \
                "%(first_name_short)s, %(gender)s/%(months)s (%(guardian)s)." \
                " %(days)s, %(ors)s") % info

        if observed:
            msg += ", " + info["observed"]

        message.respond("DIARRHEA> " + msg)
        '''
        if report.status in (report.MODERATE_STATUS,
                           report.SEVERE_STATUS,
                           report.DANGER_STATUS):
            alert = _("@%(username)s reports %(msg)s") % \
                {"username":provider.user.username, "msg":msg}
            recipients = [provider]
            for query in (Provider.objects.filter(alerts=True),
                          Provider.objects.filter(clinic=provider.clinic)):
                for recipient in query:
                    if recipient in recipients: continue
                    recipients.append(recipient)
                    message.forward(recipient.mobile, alert)
        '''

        log(case, "diarrhea_taken")
        return True

    def delete_similar(self, queryset):
        ''' Remove duplicate Diarrhea report '''
        try:
            last_report = queryset.latest("entered_at")
            if (datetime.datetime.now() - last_report.entered_at).days == 0:
                # last report was today. so delete it before filing another.
                last_report.delete()
        except models.ObjectDoesNotExist:
            pass
