#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

''' Childcount Master App

Users, Locations and Cases Management '''

import re
import time
import datetime
from functools import wraps

from django.db import models
from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from reporters.models import Role, Reporter
from locations.models import Location

from childcount.models.logs import MessageLog, log, elog
from childcount.models.general import Case, CaseNote
from childcount.models.config import Configuration as Cfg
from childcount.models.reports import ReportCHWStatus
from childcount.utils import day_start


def authenticated(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if sender property is set on message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.sender:
            return func(self, message, *args)
        else:
            message.respond(_("%(number)s is not a registered number.")
                            % {'number': message.peer})
            return True
    return wrapper


class HandlerFailed(Exception):
    ''' No function pattern matchs message '''
    pass


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"%(msg)s") \
                     % {'msg': \
                    "Sorry, only registered users can access this program."})
            return True
    return wrapper


class App(rapidsms.app.App):

    ''' ChildCount Main App

    Provides:
    User Management: join, confirm, whereami, location/loc
    Direct message: @id
    Case Management: new/nouv, cancel, innactive, activate, s/show, n/note, age
    '''

    MAX_MSG_LEN = 140
    keyword = Keyworder()
    handled = False

    def parse(self, message):

        ''' Parse incoming messages.

        flag message as not handled '''
        message.was_handled = False

    def cleanup(self, message):
        ''' log message '''
        log = MessageLog(mobile=message.peer,
                         sent_by=message.persistant_connection.reporter,
                         text=message.text,
                         was_handled=message.was_handled)
        log.save()

    def handle(self, message):
        ''' Function selector

        Matchs functions with keyword using Keyworder
        Replies formatting advices on error
        Replies on error and if no function matched '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            #message.respond(dir(self))

            command_list = [method for method in dir(self) \
                            if hasattr(getattr(self, method), 'format')]
            childcount_input = message.text.lower()
            for command in command_list:
                format = getattr(self, command).format
                try:
                    first_word = (format.split(" "))[0]
                    if childcount_input.find(first_word) > -1:
                        message.respond(format)
                        return True
                except:
                    pass

            message.respond(_("Sorry Unknown command: '%(msg)s...' " \
                              "Please try again") % {'msg': message.text[:20]})

            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e)

            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call %(mobile)s") \
                            % {'mobile': Cfg.get('developer_mobile')})

            elog(message.persistant_connection.reporter, message.text)
            raise
        message.was_handled = bool(self.handled)
        return self.handled

    @keyword(r'\@(\w+) (.+)')
    @registered
    def direct_message(self, message, target, text):
        ''' send message to any user with it ID

        Format: @[target] [message] '''
        provider = self.find_provider(message, target)
        try:
            mobile = provider.connection().identity
        except:
            self.respond_not_registered(message, target)
        sender = message.persistant_connection.reporter.alias
        return message.forward(mobile, "@%(alias)s> %(msg)s"\
                                % {'alias': sender, 'msg': text})

    keyword.prefix = ['join']

    @keyword('(\S+) (\S+) (\S+)(?: ([a-z]\w+))?')
    def join(self, message, location_code, last_name, first_name, role=None):
        ''' register as a user and join the system

        Format: join [location code] [last name] [first name]
        [role - leave blank for CHEW] '''

        #default alias for everyone until further notice
        username = None
        # do not skip roles for now
        role_code = role
        try:
            name = "%(fname)s %(lname)s" % {'fname': first_name, \
                                            'lname': last_name}
            # parse the name, and create a reporter
            alias, fn, ln = Reporter.parse_name(name)

            if not message.persistant_connection.reporter:
                rep = Reporter(alias=alias, first_name=fn, last_name=ln)
            else:
                rep = message.persistant_connection.reporter
                rep.alias = alias
                rep.first_name = fn
                rep.last_name = ln

            rep.save()

            # attach the reporter to the current connection
            message.persistant_connection.reporter = rep
            message.persistant_connection.save()

            # something went wrong - at the
            # moment, we don't care what
        except:
            message.respond(_("Join Error. Unable to register your account."))

        if role_code == None or role_code.__len__() < 1:
            role_code = Cfg.get('default_chw_role')

        reporter = message.persistant_connection.reporter

        # check location code
        try:
            location = Location.objects.get(code=location_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided location code (%(loc)s) is wrong.") \
                  % {'loc': location_code})
            return True

        # check that location is a clinic (not sure about that)
        #if not clinic.type in LocationType.objects.filter(name='Clinic'):
        #    message.forward(reporter.connection().identity, \
        #        _(u"Join Error. You must provide a Clinic code."))
        #    return True

        # set location
        reporter.location = location

        # check role code
        try:
            role = Role.objects.get(code=role_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Role code (%(role)s) is wrong.") \
                  % {'role': role_code})
            return True

        reporter.role = role

        # set account active
        # /!\ we use registered_self as active
        reporter.registered_self = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are now registered as %(role)s at %(loc)s with " \
              "alias @%(alias)s.") \
           % {'loc': location, 'role': reporter.role, 'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond(_("Success. %(reporter)s is now registered as " \
                            "%(role)s at %(loc)s with alias @%(alias)s.") \
                            % {'reporter': reporter, 'loc': location, \
                            'role': reporter.role, 'alias': reporter.alias})
        return True
    join.format = "join [location code] [last name] [first name] " \
                  "[role - leave blank for CHEW]"

    def respond_to_join(self, message, info):
        ''' replies registration informations

        message: message object to respond to
        info: a dictionary with registration infos '''
        message.respond(_("%(mobile)s registered to @%(alias)s " \
                        "(%(last_name)s %(first_name)s) at %(location)s.") \
                        % info)

    keyword.prefix = ['confirm']

    @keyword(r'(\w+)')
    def confirm_join(self, message, username):
        ''' check if a username is registered

        Format: confirm [username]'''
        try:
            user = Reporter.objects.get(alias__iexact=username)
        except object.DoesNotExist:
            self.respond_not_registered(message, username)
        user.registered_self = True
        user.save()
        info = {'mobile': user.connection().identity,
                'last_name': user.last_name.title(),
                'first_name': user.first_name.title(),
                'alias': user.alias,
                'location': user.location}
        self.respond_to_join(message, info)
        log(user, 'confirmed_join')
        return True
    confirm_join.format = "confirm [user alias]"

    def respond_not_registered(self, message, target):
        '''  raises HandlerFailed '''
        raise HandlerFailed(_("User @%(target)s is not registered.") % \
                            {'target': target})

    def find_provider(self, message, target):
        ''' Looks for a reporter id or alias in string

        message: a message to respond to
        target: a string containing an alias

        return reporter '''
        try:
            if re.match(r'^\d+$', target):
                reporter = Reporter.objects.get(id=target)
            else:
                reporter = Reporter.objects.get(alias__iexact=target)
            return reporter
        except models.ObjectDoesNotExist:
            # FIXME: try looking up a group
            self.respond_not_registered(message, target)

    # Register a new patient
    keyword.prefix = ['new', 'nouv']

    #@keyword(r'(\S+) (\S+) ([MF]) ([\d\-]+)( \D+)?( \d+)?( z\d+)?')
    @keyword(r'(.*)')
    @registered
    def new_case(self, message, token_string):
        '''Register a new patient into the system

        Format: new [patient last name] [patient first name] gender[m/f]
        [dob ddmmyy] [guardian] [contact #] [zone - optional]

        Receive patient ID number back'''
        # replace multiple spaces with a single space
        # (consider running the stringcleaning app,
        # which removes commas, cleans numbers, etc)
        whitespace = re.compile('(\s+)')
        clean_token_string = re.sub(whitespace, " ", token_string)

        # split clean_token_string by spaces
        tokens = clean_token_string.split(" ")
        self.debug(tokens)

        # create empty strings we can add to
        patient_name = ""
        guardian_name = ""
        # declare contact, since its optional
        contact = ""
        for token in tokens[:4]:
            self.debug('find patient name in first four tokens...')
            self.debug(token)

            # any tokens more than one non-digit character are probably parts
            # of the patient's name, so add to patient_name and
            # remove from tokens list
            test_age = re.match(r'(\d{1,6}[a-z]*)', token, re.IGNORECASE)

            if len(token) > 1 and not token.isdigit() and test_age is None:
                patient_name = patient_name \
                               + (tokens.pop(tokens.index(token))) + " "
                self.debug('PATIENT NAME:')
                self.debug(patient_name)

        for token in tokens:
            self.debug('TOKENS:')
            self.debug(tokens)
            self.debug('TOKEN:')
            self.debug(token)

            # attempt to match gender
            gender_matches = re.match(r'[mf]', token, re.IGNORECASE)
            if gender_matches is not None:
                self.debug('matched gender...')
                gender = token.upper()
                continue

            if token.isdigit():
                self.debug('matched contact...')
                # only save if its more than six digits
                # so we dont accidently put the dob or age in months,
                # which might sometimes match this
                if len(token) > 6:
                    contact = token
                    continue

            # attempt to match date of birth or age in months
            # if token is more than six digits, save as guardian's contact
            # this should match up between one and six digits, followed by an
            # optional word (e.g., 020301, 22m, 22mo)
            date_or_age = re.match(r'(\d{1,6}[a-z]*)', token, re.IGNORECASE)
            if date_or_age is not None:
                self.debug('matched date or age...')
                # only save if its less than six digits
                # so we dont accidently put the guardian's contact number,
                # which might sometimes match this
                if len(token) <= 6:
                    dob = token
                    continue

            # if token is letters, add it to the guardian_name
            if token.isalpha():
                self.debug('GUARDIAN NAME:')
                guardian_name = guardian_name + token + " "
                self.debug(guardian_name)
                continue

        # Strip the trailing space and partition into last and first,
        # where last contains 'lastname' and first contains either 'firstname'
        # or 'firstname secondname'
        guardian_first, sep, guardian_last = \
                                         guardian_name.rstrip().rpartition(' ')

        # Strip the trailing space and partition into last and first,
        # where last contains 'lastname' and first contains either 'firstname'
        # or 'firstname secondname'
        self.debug(patient_name)
        last, sep, first = patient_name.rstrip().rpartition(' ')

        # reporter
        reporter = message.persistant_connection.reporter

        #get language of the reporter, default to english
        lang = message.persistant_connection.reporter.language
        if not lang:
            lang = 'en'

        location_code = message.persistant_connection.reporter.location.code
        self.debug('location_code= ' + location_code)
        self.debug(dob)

        # remove all non-digit characters from dob string
        dob = re.sub(r'\D', '', dob)
        estimated_dob = False # set this now to avoid error if we dont match
        self.debug(dob)

        # if there are three or more digits, we are
        # probably dealing with a date
        if len(dob) >= 3:
            try:
                # TODO this 2 step conversion is too complex, simplify!
                dob = time.strptime(dob, "%d%m%y")
                dob = datetime.date(*dob[:3])
            except ValueError:
                try:
                    # TODO this 2 step conversion is too complex, simplify!
                    dob = time.strptime(dob, "%d%m%Y")
                    dob = datetime.date(*dob[:3])
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %(dob)s")\
                                        % {'dob': dob})
            self.debug(dob)

        # if there are fewer than three digits, we are
        # probably dealing with an age (in months),
        # so attempt to estimate a dob
        else:
            # TODO move to a utils file? (almost same code in import_cases.py)
            try:
                if dob.isdigit():
                    years = int(dob) / 12
                    months = int(dob) % 12
                    est_year = abs(datetime.date.today().year - int(years))
                    est_month = abs(datetime.date.today().month - int(months))
                    if est_month == 0:
                        est_month = 1
                    estimate = ("%s-%s-%s" % (est_year, est_month, 15))
                    # TODO this 2 step conversion is too complex, simplify!
                    dob = time.strptime(estimate, "%Y-%m-%d")
                    dob = datetime.date(*dob[:3])
                    self.debug(dob)
                    estimated_dob = True
            except Exception, e:
                self.debug(e)

        # Concatenate Mother's name
        guardian = "%s %s" % (guardian_last, guardian_first)

        # compute location
        if location_code == "":
            # reporter wants to reuse last location
            try:
                today = datetime.datetime.now
                today = today.replace(hour=0, minute=0, second=0)
                location = list(Case.objects.filter(reporter=reporter, \
                                created_at__gte=today).all())[-1].location
            except:
                message.respond(_(u"Can't figure out where you are today. " \
                                "Please use message: Location locationcode " \
                                "to set your location."))
                return True
        else:
            try:
                location = Location.objects.get(code=location_code)
            except:
                message.respond(_(u"Can't find your location based on the " \
                                "code your sent. Please resend."))
                return True

        # store case info in object
        info = {
            'first_name': first.title(),
            'last_name': last.title(),
            'gender': gender.upper()[0],
            'dob': dob,
            'estimated_dob': estimated_dob,
            'guardian': guardian.title(),
            'mobile': contact,
            'reporter': reporter,
            'location': location}

        ## check to see if the case already exists
        iscase = Case.objects.filter(first_name=info['first_name'], \
                                     last_name=info['last_name'], \
                                     reporter=info['reporter'], \
                                     dob=info['dob'])
        if iscase:
            info['PID'] = iscase[0].ref_id
            self.info(iscase[0].id)
            self.info(info)
            message.respond(_("%(last_name)s, %(first_name)s (+%(PID)s) " \
                            "has already been registered by %(reporter)s.") \
                            % info)
            # TODO: log this message
            return True
        case = Case(**info)
        case.save()

        info.update({
            'id': case.ref_id,
            'last_name': last.upper(),
            'age': case.age()})
        #set up the languages
        msg = {}

        msg['en'] = "New +%(id)s: %(last_name)s, %(first_name)s " \
                    "%(gender)s/%(age)s (%(guardian)s) %(location)s" % info
        msg['fr'] = "Nouv +%(id)s: %(last_name)s, %(first_name)s " \
                    "%(gender)s/%(age)s (%(guardian)s) %(location)s" % info
        message.respond(_("%s") % msg[lang])


        log(case, 'patient_created')
        return True
    new_case.format = "[new/nouv] [patient last name] [patient first name] " \
                      "gender[m/f] [dob ddmmyy] [guardian] (contact #)"

    def find_case(self, ref_id):
        '''look up a patient id

        return case
        '''
        try:
            return Case.objects.get(ref_id=int(ref_id))
        except Case.DoesNotExist:
            raise HandlerFailed(_("Case +%(ref_id)s not found.") % \
                                {'ref_id': ref_id})

    keyword.prefix = ['cancel']

    @keyword(r'\+?(\d+)')
    @registered
    def cancel_case(self, message, ref_id):
        '''Cancel a case

        Format: cancel [ref_id]
        ref_id: case reference number

        cancels a case only if that case has no other report associated '''

        case = self.find_case(ref_id)
        if case.reportmalnutrition_set.count():
            raise HandlerFailed(_("Cannot cancel +%(ref_id)s: "\
                    "case has malnutrition reports.") % {'ref_id': ref_id})

        if case.reportmalaria_set.count():
            raise HandlerFailed(_("Cannot cancel +%(ref_id)s: "\
                        "case has malaria reports.") % {'ref_id': ref_id})

        if case.reportdiagnosis_set.count():
            raise HandlerFailed(_("Cannot cancel +%(ref_id)s: "\
                    "case has diagnosis reports.") % {'ref_id': ref_id})

        case.delete()
        message.respond(_("Case +%(ref_id)s cancelled.") % {'ref_id': ref_id})


        log(message.persistant_connection.reporter, 'case_cancelled')
        return True
    cancel_case.format = "cancel [patient id number]"

    keyword.prefix = ['inactive']

    @keyword(r'\+?(\d+)?(.+)')
    @registered
    def inactive_case(self, message, ref_id, reason=""):
        '''set case status to inactive.

        Format: inactive [ref_id] [reason]
        ref_id: case reference number
        reason (optional): free text explaination '''

        case = self.find_case(ref_id)
        case.set_status(Case.STATUS_INACTIVE)
        case.save()
        info = case.get_dictionary()
        message.respond(_("+%(ref_id)s: %(last_name)s, %(first_name)s " \
                        "%(gender)s/%(months)s (%(guardian)s) has been " \
                        "made inactive") % info)
        return True
    inactive_case.format = "inactive [patient id] [reason]"

    keyword.prefix = ['activate']

    @keyword(r'\+?(\d+)?(.+)')
    @registered
    def activate_case(self, message, ref_id, reason=""):
        '''set case status to active.

        Format: activate [ref_id] [reason]
        ref_id: case reference number
        reason (optional): free text explaination '''
        case = self.find_case(ref_id)
        info = case.get_dictionary()

        if case.status == Case.STATUS_INACTIVE:
            case.set_status(Case.STATUS_ACTIVE)
            case.save()
            message.respond(_("+%(ref_id)s: %(last_name)s, %(first_name)s " \
                            "%(gender)s/%(months)s (%(guardian)s) "\
                            "has been activated") % info)
        elif case.status == Case.STATUS_ACTIVE:
            message.respond(_("+%(ref_id)s: %(last_name)s, %(first_name)s "\
                            "%(gender)s/%(months)s (%(guardian)s) " \
                            "is active") % info)
        elif case.status == Case.STATUS_DEAD:
            message.respond(_("+%(ref_id)s: %(last_name)s, %(first_name)s " \
                            "%(gender)s/%(months)s (%(guardian)s) " \
                            "was reported as dead") % info)
        return True
    activate_case.format = "activate +[patient ID] [your reasons]"

    keyword.prefix = ['activity']

    @keyword(r'?(\w+)')
    @keyword.blank()
    @registered
    def activity_summary(self, message, period=None):
        '''Get a reporters activity summary'''
        reporter = message.persistant_connection.reporter
        duration_end = datetime.datetime.now()
        if period is None or period.lower() == "all":
            ml = MessageLog.objects.filter(sent_by=reporter)\
                    .order_by('created_at')
            if ml:
                duration_start = ml[0].created_at
        elif period.lower() == "month":
            last_30_days = datetime.timedelta(30)
            duration_start = duration_end - last_30_days
        elif period.lower() == "week":
            last_seven_days = datetime.timedelta(7)
            duration_start = duration_end - last_seven_days
        elif period.lower() == "day":
            duration_start = day_start(datetime.datetime.today())
        else:
            duration_start = None
            msg = "No Summary"

        if duration_start is not None:
            summary = ReportCHWStatus.reporter_summary(duration_start, \
                                                duration_end, reporter)

            msg = _("%(reporter)s: %(num_cases)s children, "\
                "#new %(num_new_cases)s, #dead %(num_dead)s, "\
                "#inactive %(num_cases_inactive)s" \
                ", #mrdt %(num_malaria_reports)s, #muac %(num_muac)s. ")\
                 % summary

        message.respond(_("%s") % msg)
        return True
    activity_summary.format = "activity [day|week|month|all]"

    keyword.prefix = ['transfer']

    @keyword(r'\+?(\d+) (?:to )?\@?(\w+)')
    @registered
    def transfer_case(self, message, ref_id, target):
        '''Transfer case from one reporter to another

        Format: transfer [ref_id] [target]
        ref_id: case reference number
        target: alias of the CHW/Reporter to transfer to '''
        reporter = message.persistant_connection.reporter
        case = self.find_case(ref_id)
        new_provider = self.find_provider(message, target)
        case.reporter = new_provider
        case.save()
        info = {
            'username': new_provider.alias,
            'name': new_provider.full_name(),
            'location': new_provider.location}
        info['ref_id'] = case.ref_id
        message.respond(_("Case +%(ref_id)s transferred to @%(username)s " \
                        "(%(name)s - %(location)s).") % info)

        message.forward(new_provider.connection().identity,
                        _("Case +%(ref_id)s transferred to you from "\
                          "@%(username)s (%(name)s - %(location)s).") % \
                        info)

        log(case, 'case_transferred')
        return True
    transfer_case.format = "transfer [patient id] [new person in charge of " \
                           "the patient]"

    keyword.prefix = ['s', 'show']

    @keyword(r'\+?(\d+)')
    @registered
    def show_case(self, message, ref_id):
        ''' replies case details

        Format: show [ref_id]
        ref_id: case reference number '''
        case = self.find_case(ref_id)
        info = case.get_dictionary()

        message.respond(_("+%(ref_id)s %(status)s %(last_name)s, " \
                        "%(first_name)s %(gender)s/%(age)s %(guardian)s - " \
                        "%(location)s") % info)

        return True
    show_case.format = "show [patient id]"

    keyword.prefix = ['n', 'note']

    @keyword(r'\+(\d+) (.+)')
    @registered
    def note_case(self, message, ref_id, note):
        ''' Annotate Case

        Format: note [ref_id] [note]
        ref_id: case reference number
        note: free text note '''
        reporter = message.persistant_connection.reporter
        case = self.find_case(ref_id)
        CaseNote(case=case, created_by=reporter, text=note).save()
        message.respond(_("Note added to case +%(ref_id)s.") % \
                        {'ref_id': ref_id})

        log(case, 'note_added')
        return True
    note_case.format = "note [patient id] [your note]"

    #Whereami
    keyword.prefix = ['whereami']

    @keyword.blank()
    @registered
    def whereami(self, message):
        ''' replies location of sender '''
        reporter = message.persistant_connection.reporter

        info = {'reporter': reporter,
                'location': reporter.location,
                'loc_code': reporter.location.code}

        message.respond(_("You are in %(location)s (%(loc_code)s)") % info)

        return True

    #change location
    keyword.prefix = ['location', 'loc']

    @keyword(r'(slug)')
    @registered
    def change_location(self, message, location_code):
        ''' change location of sender

        Format: location [location_code]
        location_code: location code string'''
        reporter = message.persistant_connection.reporter

        # check location code
        try:
            location = Location.objects.get(code=location_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                            _(u"Location Error. Provided location code " \
                            "(%(loc)s) is wrong.") % {'loc': location_code})
            return True

        reporter.location = location
        reporter.save()

        info = {'reporter': reporter,
                'location': reporter.location,
                'loc_code': reporter.location.code}

        message.respond(_("Your location is now %(location)s (%(loc_code)s)") \
                        % info)

        return True

    #assane
    # Modify dob of patient
    keyword.prefix = ['age']

    #@keyword(r'\+?(\d+) ([\d\-]+)')
    @keyword(r'\+?(\d+) (\d{1,6}[a-z\-]*)')
    @registered
    def update_age(self, message, ref_id, dob):
        ''' Update patient date of birth

        Format: age [ref_id] [dob]
        ref_id: case id
        dob: date of birth string

        replies back patient ID '''
        self.debug('update_age ...')
        # reporter
        reporter = message.persistant_connection.reporter



        # attempt to match date of birth or age in months
        # if token is more than six digits, save as guardian's contact
        # this should match up between one and six digits, followed by an
        # optional word (e.g., 020301, 22m, 22mo)
        date_or_age = re.match(r'(\d{1,6}[a-z\-]*)', dob, re.IGNORECASE)
        if date_or_age is not None:
            self.debug('matched date or age...')
            # only save if its less than six digits
            # so we dont accidently put the guardian's contact number,
            # which might sometimes match this
            if len(dob) <= 6:
                dob = dob

        # remove all non-digit characters from dob string
        dob = re.sub(r'\D', '', dob)
        estimated_dob = False # set this now to avoid error if we dont match
        self.debug(dob)

        # if there are three or more digits, we are
        # probably dealing with a date
        if len(dob) >= 3:
            try:
                # TODO this 2 step conversion is too complex, simplify!
                dob = time.strptime(dob, "%d%m%y")
                dob = datetime.date(*dob[:3])
            except ValueError:
                try:
                    # TODO this 2 step conversion is too complex, simplify!
                    dob = time.strptime(dob, "%d%m%Y")
                    dob = datetime.date(*dob[:3])
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %(dob)s")\
                                     % {'dob': dob})
            self.debug(dob)

        # if there are fewer than three digits, we are
        # probably dealing with an age (in months),
        # so attempt to estimate a dob
        else:
            # TODO move to a utils file? (almost same code in import_cases.py)
            try:
                if dob.isdigit():
                    years = (int(dob)) / 12
                    months = (int(dob)) % 12
                    est_year = abs(datetime.date.today().year - int(years))
                    delta=datetime.date.today().month - int(months)
                    if delta==0:
                       est_month = months
                    else:
                        if delta<0:
                           est_month = 12 + datetime.date.today().month - months 
                           est_year=est_year-1 
                        else:
                            est_month=delta
                    estimate = ("%s-%s-%s" % (est_year, est_month, 15))
                    # TODO this 2 step conversion is too complex, simplify!
                    dob = time.strptime(estimate, "%Y-%m-%d")
                    dob = datetime.date(*dob[:3])
                    self.debug(dob)
                    estimated_dob = True

            except Exception, e:
                self.debug(e)

        delta = datetime.datetime.now().date() - dob
        years = delta.days / 365.25
        if years < 0:
            raise HandlerFailed(_("The age couldn't be greater than "\
                    "the date now, please retape the date!!! "))

        # todo: move this to a more generic get_description
        info = {
            'ref_id': ref_id,
            'dob': dob}

        ## check to see if the case already exists
        iscase = Case.objects.filter(ref_id=info['ref_id'])
        if iscase.count() == 1:
            first_case = iscase[0]
            #iscase = Case(**info)
            first_case.dob = info['dob']
            first_case.save()
        else:
            message.respond(_(" The patient %(ref_id)s is not registred.") \
                            % info)
            # TODO: log this message
            return True
        info.update({
            'id': first_case.ref_id,
            'dob': first_case.age()})

        message.respond(_("l'age du patient +%(id)s a ete modifie, il est " \
                        "maintenant age de %(dob)s") % info)

        #log(first_case, "age_patient_update")
        return True
