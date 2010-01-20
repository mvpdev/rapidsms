#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Malnutrition App

Records MUAC measurements
'''

import re
import datetime
from functools import wraps

from django.db import models
from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from childcount.models.logs import MessageLog, log
from childcount.models.general import Case
from childcount.models.config import Configuration as Cfg
from muac.models import ReportMalnutrition, Observation
from reporters.models import PersistantBackend


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this program.%(msg)s") % {'msg': ""})

            return True
    return wrapper


class HandlerFailed (Exception):
    pass


class App (rapidsms.app.App):

    ''''Malnutrition main App

    Records MUAC measurements - muac
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

    def get_observations(self, text):
        choices = dict([(o.letter, o) for o in Observation.objects.all()])
        observed = []
        if text:
            text = re.sub(r'\W+', ' ', text).lower()
            for observation in text.split(' '):
                obj = choices.get(observation, None)
                if not obj:
                    if observation != 'n':
                        raise HandlerFailed(_("Unknown observation code: %(ob)s")\
                                             % {'ob': observation})
                else:
                    observed.append(obj)
        return observed, choices

    def delete_similar(self, queryset):
        try:
            last_report = queryset.latest('entered_at')
            if (datetime.datetime.now() - last_report.entered_at).days == 0:
                # last report was today. so delete it before filing another.
                last_report.delete()
        except models.ObjectDoesNotExist:
            pass

    def get_muac_report_format_reminder(self):
        '''Expected format for muac command, sent as a reminder'''
        return "Format:  muac +[patient_ID\] muac[measurement] edema[e/n]"\
                " symptoms separated by spaces[CG D A F V NR UF]"

    keyword.prefix = ['muac', 'pb']

    @keyword(r'\+(\d+) ([\d\.]+)?( [\d\.]+)?( [\d\.]+)?( (?:[a-z]\s*)+)?')
    @registered
    def report_case(self, message, ref_id, muac=None,
                     weight=None, height=None, complications=''):
        '''Record  muac, weight, height, complications if any

        Format:  muac +[patient_ID\] muac[measurement] edema[e/n]
                 symptoms separated by spaces[CG D A F V NR UF]

        reply with diagnostic message
        '''
        # TODO use gettext instead of this dodgy dictionary
        _i = {
                'units': {'MUAC': 'mm', 'weight': 'kg', 'height': 'cm'},
                'en': {'error': "Can't understand %s (%s): %s"},
                'fr': {'error': "Ne peux pas comprendre %s (%s): %s"}}

        def guess_language(msg):
            if msg.upper().startswith('MUAC'):
                return 'en'
            if msg.upper().startswith('PB'):
                return 'fr'

        # use reporter's preferred language, if possible
        if message.reporter:
            if message.reporter.language is not None:
                lang = message.reporter.language
            else:
                # otherwise make a crude guess
                lang = guess_language(message.text)
                message.reporter.language = lang
        else:
            lang = 'fr'

        # if there is no height, ASSUME that muac is the (newly) optional
        # field that has been omitted. swap weight and height to their
        # ASSUMED values. TODO change the order of the fields in the form
        if height is None:
            wt = weight
            mu = muac
            weight = mu
            height = wt

        case = self.find_case(ref_id)
        try:
            muac = float(muac)
            if muac < 30: # muac is in cm?
                muac *= 10
            muac = int(muac)
        except ValueError:
            raise HandlerFailed((_i[lang] % ('MUAC', _i['units']['MUAC'], \
                                              muac)))
                #_("Can't understand MUAC (mm): %s") % muac)

        if weight is not None:
            try:
                weight = float(weight)
                if weight > 100:
                    # weight is in g?
                    weight /= 1000.0
            except ValueError:
                #raise HandlerFailed("Can't understand weight (kg):
                #%s" % weight)
                raise HandlerFailed((_i[lang] % ('weight', \
                                    _i['units']['weight'], weight)))

        if height is not None:
            try:
                height = float(height)
                if height < 3: # weight height in m?
                    height *= 100
                height = int(height)
            except ValueError:
                #raise HandlerFailed("Can't understand height (cm):
                # %s" % height)
                raise HandlerFailed((_i[lang] % ('height', \
                                _i['units']['height'], height)))

        observed, choices = self.get_observations(complications)
        self.delete_similar(case.reportmalnutrition_set)

        reporter = message.persistant_connection.reporter
        report = ReportMalnutrition(case=case, reporter=reporter, muac=muac,
                        weight=weight, height=height)
        report.save()
        for obs in observed:
            report.observed.add(obs)
        report.diagnose()
        report.save()

        #choice_term = dict(choices)

        info = case.get_dictionary()
        info.update(report.get_dictionary())

        msg = _("%(diagnosis_msg)s. +%(ref_id)s %(last_name)s, "\
            "%(first_name_short)s, %(gender)s/%(months)s (%(guardian)s). "\
            "MUAC %(muac)s") % info

        if weight:
            msg += ", %.1f kg" % weight
        if height:
            msg += ", %.1d cm" % height
        if observed:
            msg += ', ' + info['observed']

        #get the last reported muac b4 this one
        last_muac = report.get_last_muac()
        if last_muac is not None:
            psign = "%"
            #take care for cases when testing using httptester, %
            #sign prevents feedback.
            if PersistantBackend.from_message(message).title == "http":
                psign = "&#37;"
            last_muac.update({'psign': psign})
            msg += _(". Last MUAC (%(reported_date)s): %(muac)s "\
                     "(%(percentage)s%(psign)s)") % last_muac

        msg = "MUAC> " + msg
        if len(msg) > self.MAX_MSG_LEN:
                    message.respond(msg[:msg.rfind('. ') + 1])
                    message.respond(msg[msg.rfind('. ') + 1:])
        else:
            message.respond(msg)

        if report.status in (report.MODERATE_STATUS,
                           report.SEVERE_STATUS,
                           report.SEVERE_COMP_STATUS):
            alert = _("@%(username)s reports %(msg)s [%(mobile)s]")\
                 % {'username': report.reporter.alias, 'msg': msg, \
                    'mobile': reporter.connection().identity}

            recipients = report.get_alert_recipients()
            for recipient in recipients:
                if len(alert) > self.MAX_MSG_LEN:
                    message.forward(recipient.connection().identity, \
                                    alert[:alert.rfind('. ') + 1])
                    message.forward(recipient.connection().identity, \
                                    alert[alert.rfind('. ') + 1:])
                else:
                    message.forward(recipient.connection().identity, alert)

        log(case, 'muac_taken')
        return True
    report_case.format = "muac +[patient_ID\] muac[measurement] edema[e/n]"\
                " symptoms separated by spaces[CG D A F V NR UF]"
