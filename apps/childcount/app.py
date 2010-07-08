#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import time
from datetime import datetime, timedelta

from django.utils.translation import ugettext as _, activate
from django.utils.translation import ungettext
from django.db import models
from reversion import revision

import rapidsms
from reporters.models import Reporter
from locations.models import Location
from scheduler.models import EventSchedule

from childcount.models import Configuration as Cfg
from childcount.models import Patient, Encounter, FormGroup, CHW
from childcount.forms import *
from childcount.commands import *
from childcount.exceptions import *
from childcount.schedules import *
from childcount.utils import respond_exceptions, KeywordMapper


class App (rapidsms.app.App):
    """Main ChildCount App
    """
    DEFAULT_LANGUAGE = 'en'
    FORM_PREFIX = '+'

    # The time at which we decide this is a new encounter, in MINUTES
    ENCOUNTER_TIMEOUT = 6 * 60

    commands = []
    forms = []

    def configure(self, title='ChildCount', tab_link='/childcount', \
                  forms=None, commands=None):
        if forms is not None:
            forms = forms.replace(' ', '').split(',')
            for form in forms:
                try:
                    self.forms.append(eval(form))
                except NameError:
                    self.debug(_(u'%s form not found.') % form)
        if commands is not None:
            commands = commands.replace(' ', '').split(',')
            for command in commands:
                try:
                    self.commands.append(eval(command))
                except:
                    self.debug(_(u'%s command not found.') % command)

    def start(self):
        self.command_mapper = KeywordMapper()
        self.form_mapper = KeywordMapper()
        self.form_mapper.add_classes(self.forms)
        self.command_mapper.add_classes(self.commands)

    def parse(self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    @respond_exceptions
    @revision.create_on_success
    def handle(self, message):
        handled = False


        # If this is coming from debackend, it will have message.chw and
        # message.encounter_date.  Otherwise, the reporter is the chw,
        # and the encounter date is from the backend
        if 'chw' in message.__dict__:
            try:
                chw = CHW.objects.get(pk=message.chw)
            except CHW.DoesNotExist:
                message.respond(_(u"Problem getting CHW from backend."), \
                                'error')
                return handled
            reporter = chw.reporter
            message.reporter = reporter
        else:
            reporter = message.persistant_connection.reporter

        if reporter and reporter.language:
            lang = reporter.language
        else:
            lang = self.DEFAULT_LANGUAGE

            # store default language in reporter during session
            if reporter:
                reporter.language = lang

        activate(lang)

        # Use the datetime coming from the backend as the date. Times
        # from the backend are UTC naive. We convert it to localtime
        # naive. The system clock of the server must be set to the
        # local time zone for this to work. This won't work correctly
        # for locations with DST.
        message.date = message.date - timedelta(seconds=time.timezone)

        # Set the user of revision, equal to the user object of the reporter
        if reporter:
            revision.user = reporter.user_ptr

        # make lower case, strip, and remove duplicate spaces
        input_text = re.sub(r'\s{2,}', ' ', message.text.strip().lower())

        ### Forms
        split_regex = re.compile( \
         r'^\s*((?P<health_ids>.*?)\s*)??(?P<forms>%(form_prefix)s.+$)' % \
             {'form_prefix': re.escape(self.FORM_PREFIX)})
        forms_match = split_regex.match(input_text)

        if forms_match:
            handled = True
            if not reporter:
                message.respond(_(u"You must register before you can send"\
                                  u" reports."), 'error')
                return handled

            chw = reporter.chw
            if 'encounter_date' in message.__dict__:
                try:
                    date = datetime.strptime(message.encounter_date, \
                                             "%Y-%m-%d")
                    # set it to midday on that day...
                    message.date = date + timedelta(hours=12)
                except ValueError:
                    message.respond(_(u"Problem getting encounter_date from "\
                                       "backend."), 'error')
                    return handled
            encounter_date = message.date

            health_ids_text = forms_match.groupdict()['health_ids']
            forms_text = forms_match.groupdict()['forms']
            if health_ids_text:
                health_ids = re.findall(r'\w+', health_ids_text)
            else:
                health_ids = []

            form_groups_regex = re.compile( \
                r'%(form_prefix)s\s?(\w+.*?)(?=\s*%(form_prefix)s|$)' % \
                 {'form_prefix': re.escape(self.FORM_PREFIX)})

            forms = []
            for group in form_groups_regex.findall(forms_text):
                params = re.split(r'\s+', group)
                forms.append(params)

            # okay, health_ids is a list containing all health ids:
            # i.e: ['df2d', 'se23', 'di24']

            # forms is a list of lists containing the forms and
            # thier params:
            # i.e: [['birth', 'p', 'm'], ['h', 'y'], ['mob', '12345678']]

            # Write now, we are only going to accept a single health ID.
            if len(health_ids) != 1:
                message.respond(_(u"Error: Message not understood. " \
                                   "Your message must start with " \
                                   "a single health ID, followed by a space " \
                                   "then a %(pre)s, then the keyword of the " \
                                   "form you are sending.") % \
                                   {'pre': self.FORM_PREFIX}, 'error')
                return handled
            health_id = health_ids[0]

            failed_forms = []
            successful_forms = []

            pre_processed_form_objects = []
            for params in forms:
                keyword = params[0]

                if keyword not in self.form_mapper.get_keywords(lang):
                    failed_forms.append({'keyword': keyword, \
                                        'error': _(u"Not a recognised form.")})
                    continue
                cls = self.form_mapper.get_class(lang, keyword)
                form = cls(message, encounter_date, chw, params, health_id)

                # First process.  This is where PatientRegistration will
                # create the patient records
                try:
                    form.pre_process()
                except CCException, e:
                    pretty_form = '%s%s' % (self.FORM_PREFIX, \
                                            keyword.upper())

                    message.respond(_(u"Error occurred while processing " \
                                      "%(frm)s: %(e)s Please correct and " \
                                      "send all information again.") % \
                                       {'frm': pretty_form, 'e': e}, \
                                        'error')
                    return handled
                pre_processed_form_objects.append(form)

            # Now that we have run pre-process, health_id should point to a
            # valid paitent (new patients are created in the
            # PatientRegistrationForm pre_process method
            try:
                patient = Patient.objects.get(health_id__iexact=health_id)
            except Patient.DoesNotExist:
                message.respond(_(u"%(id)s is not a valid health ID. " \
                                   "Please correct and try again.") % \
                                   {'id': health_id}, 'error')
                return handled

            # If all of the forms are household forms and the patient is not
            # head of household, don't proceed to process.  If there is one
            # or more household forms mixed with one or more individual forms
            # that will get caught later.
            patient_filter = lambda form: form.ENCOUNTER_TYPE == \
                                                       Encounter.TYPE_PATIENT
            patient_forms = filter(patient_filter, \
                                   pre_processed_form_objects)
            if len(patient_forms) == 0 and not patient.is_head_of_household():
                message.respond(_(u"Error: You tried to send househould " \
                                  "forms for someone who is not head of" \
                                  "household. You must send the forms with " \
                                  "the head of household health ID." \
                                  "Their head of household health ID " \
                                  "is %(hoh)s (Health ID: %(hohid)s)") % \
                              {'hoh': patient.household.full_name(), \
                               'hohid': patient.household.health_id.upper()}, \
                               'error')

                return handled

            encounters = {}
            encounters[Encounter.TYPE_PATIENT] = None
            encounters[Encounter.TYPE_HOUSEHOLD] = None

            form_groups = {}
            form_groups[Encounter.TYPE_PATIENT] = None
            form_groups[Encounter.TYPE_HOUSEHOLD] = None
            for form in pre_processed_form_objects:
                keyword = form.params[0]

                if form.ENCOUNTER_TYPE == Encounter.TYPE_HOUSEHOLD and \
                   not patient.is_head_of_household():
                    failed_forms.append({'keyword': keyword, \
                                         'error': _(u"This form is only for " \
                                                    "head of households.")})
                    continue

                # If we haven't created the encounter objects, we'll create
                # them now.
                if encounters[form.ENCOUNTER_TYPE] is None:
                    try:
                        encounters[form.ENCOUNTER_TYPE] = \
                            Encounter.objects.filter(chw=chw, \
                                 patient=patient, \
                                 type=form.ENCOUNTER_TYPE)\
                                 .latest('encounter_date')
                        if not encounters[form.ENCOUNTER_TYPE].is_open == True:
                            raise Encounter.DoesNotExist
                    except Encounter.DoesNotExist:
                        encounters[form.ENCOUNTER_TYPE] = \
                                    Encounter(chw=chw, patient=patient, \
                                              type=form.ENCOUNTER_TYPE, \
                                              encounter_date=encounter_date)
                        encounters[form.ENCOUNTER_TYPE].save()

                    form_groups[form.ENCOUNTER_TYPE] = FormGroup(
                           entered_by=reporter, \
                           backend=message.persistant_connection.backend, \
                           encounter=encounters[form.ENCOUNTER_TYPE])
                    form_groups[form.ENCOUNTER_TYPE].save()

                # Set encounter and form_group in the Form object to the ones
                # created above
                form.encounter = encounters[form.ENCOUNTER_TYPE]
                form.form_group = form_groups[form.ENCOUNTER_TYPE]

                try:
                    form.process(patient)
                except CCException, e:
                    failed_forms.append({'keyword': keyword, \
                                         'error': unicode(e), 'e': e})
                else:
                    successful_forms.append({'keyword': keyword, \
                                             'response': form.response, \
                                             'obj': form})
                    # Append this successful form class name to the comma
                    # delimited list in FormGroup.
                    class_name = form.__class__.__name__
                    if not form_groups[form.ENCOUNTER_TYPE].forms:
                        form_groups[form.ENCOUNTER_TYPE].forms = class_name
                    else:
                        form_groups[form.ENCOUNTER_TYPE].forms += \
                                                               ',' + class_name
                    form_groups[form.ENCOUNTER_TYPE].save()

            for form_type in [Encounter.TYPE_PATIENT, \
                              Encounter.TYPE_HOUSEHOLD]:
                # Delete the form_group objects if there weren't any successful
                # forms.
                if form_groups[form_type] and not form_groups[form_type].forms:
                    form_groups[form_type].delete()

                # At this point, if the encounter object doesn't have a single
                # FormGroup pointing to it, then no forms were successful this
                # time and there were no previously successful forms for that
                # encounter, so we delete it
                if encounters[form_type] and \
                   encounters[form_type].formgroup_set.all().count() == 0:
                    encounters[form_type].delete()

            successful_string = ''
            if successful_forms:
                print successful_forms
                keywords = [self.FORM_PREFIX + f['keyword'].upper() \
                                                   for f in successful_forms]
                successful_string += ', '.join(keywords) + \
                                                _(u" Successfully processed:")

                for form in successful_forms:
                    successful_string += ' [%s]' % form['response']

            failed_string = ''
            send_again = False
            for form in failed_forms:
                failed_string += ' %(pre)s%(keyword)s failed: %(error)s' % \
                                 {'pre': self.FORM_PREFIX, \
                                  'keyword': form['keyword'].upper(), \
                                  'error': form['error']}
                if 'e' in form and not isinstance(form['e'], Inapplicable):
                    send_again = True
            if send_again and len(failed_forms) == 1:
                failed_string += _(" You must resend the form.")
            elif send_again and len(failed_forms) > 1:
                failed_string += _(" You must resend the forms.")

            if successful_forms and not failed_forms:
                message.respond(successful_string, 'success')
                return handled
            if failed_forms and not successful_forms:
                message.respond(failed_string, 'error')
                return handled
            else:
                if len(failed_forms) == 1:
                    cnt_failed = _(u"One form failed.")
                else:
                    cnt_failed = _(u"%d forms failed.") % len(failed_forms)

                if len(successful_forms) == 1:
                    cnt_successful = _(u"One successful.")
                else:
                    cnt_successful = _(u"%d forms successful.") % \
                                                        len(successful_forms)
                response = u"%s, %s: %s, %s" % (cnt_failed, cnt_successful, \
                                                failed_string, \
                                                successful_string)
                message.respond(response, 'warning')
            return handled

        ### Commands
        params = re.split(r'\s+', input_text)
        command = params[0]
        if command in self.command_mapper.get_keywords(lang):
            handled = True
            cls = self.command_mapper.get_class(lang, command)
            obj = cls(message, params)
            try:
                obj.process()
            except CCException, e:
                message.respond(e.message, 'error')
        return handled

    def cleanup(self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing(self, message):
        """Handle outgoing message notifications."""
        pass

    def stop(self):
        """Perform global app cleanup when the application is stopped."""
        pass
