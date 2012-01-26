#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

from datetime import date as pydate, datetime

from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import *

from apps.reporters.models import *
from apps.locations.models import *
from apps.findug.models import *
from apps.findug.utils import *


class HandlerFailed (Exception):
    pass


class MalformedRequest (Exception):
    pass


class AmbiguousAlias (Exception):
    pass


def registered(func):

    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users "
                               "can access this program."))
            return True
    return wrapper


def admin(func):

    def wrapper(self, message, *args):
        reporter = message.persistant_connection.reporter
        if reporter and \
           ReporterGroup.objects.get(title='admin') in reporter.groups.only():
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only administrators of "
                               "the system can perform this action."))
            return False
    return wrapper


def rec_type_from_string(rec_type):
    if rec_type == '@':
        rec_type = None
    if rec_type == '@@':
        rec_type = Reporter
    if rec_type == '@@@':
        rec_type = Location
    return rec_type


def peer_from_alias(alias, of_type=None):

    try:
        reporter = Reporter.objects.get(alias=alias)
    except models.ObjectDoesNotExist:
        reporter = None

    try:
        location = Location.objects.get(code=alias)
    except models.ObjectDoesNotExist:
        location = None

    if reporter and location:
        if of_type and of_type.__class__ == django.db.models.base.ModelBase:
            return reporter if of_type == Reporter else location
        elif of_type:
            return reporter, location
        else:
            raise AmbiguousAlias

    return reporter if reporter else location


class App (rapidsms.app.App):

    keyword = Keyworder()

    def start(self):
        pass

    def handle(self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            message.respond(_(u"Error. Your message could not be recognized "
                               "by the system. Please check and try again."))
            return False
        try:
            handled = func(self, message, *captures)
        except HandlerFailed, e:
            print e
            handled = True
        except Exception, e:
            print e
            message.respond(_(u"An error has occured (%(e)s).") % {'e': e})
            raise
        message.was_handled = bool(handled)
        return handled

    ############################
    #  REGISTRATION
    ############################

    # SUBSCRIBE
    keyword.prefix = ["subscribe"]

    @keyword(r'(\w+) (.+)')
    def join(self, message, clinic_code, name):
        ''' register a user and join the system '''

        # skip roles for now
        role_code = None

        try:
            clinic = HealthUnit.objects.get(code=clinic_code.lower())
        except models.ObjectDoesNotExist:
            message.respond(_(u"Subscribe error. Provided health unit "
                               "code (%(clinic)s) is wrong.") %
                               {'clinic': clinic_code})
            return True

        try:
            # parse the name, and create a reporter
            alias, fn, ln = Reporter.parse_name(name.replace('.', ' ').strip())

            if not message.persistant_connection.reporter:
                rep = Reporter(alias=alias[:20], first_name=fn, last_name=ln)
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
            message.respond(u"Subscribe error. "
                             "Unable to register your account.")
            return True

        if role_code == None or role_code.__len__() < 1:
            role_code = 'hw'

        reporter = message.persistant_connection.reporter

        return self.join_reporter(message, reporter, clinic_code, role_code)

    # JOIN
    keyword.prefix = ["join"]

    @keyword(r'(\w+)')
    @registered
    def join(self, message, clinic_code):
        ''' Adds a self-registered reporter to the system '''

        # skip roles for now
        role_code = None

        if role_code == None or role_code.__len__() < 1:
            role_code = 'hw'

        reporter = message.persistant_connection.reporter

        return self.join_reporter(message, reporter, clinic_code, role_code)

    # JOIN (ADMIN)
    keyword.prefix = ["join"]

    @keyword(r'\@(slug) (letters)\s?(\w*)')
    @registered
    @admin
    def join_one(self, message, reporter_alias, clinic_code):
        ''' Adds an arbitrary reporter to the mrdt system '''

        # skip roles for now
        role_code = None

        if role_code == None or role_code.__len__() < 1:
            role_code = 'hw'

        try:
            reporter = Reporter.objects.get(alias=reporter_alias)
        except models.ObjectDoesNotExist:
            message.respond(_(u"Join Error. The provided alias (%(alias)s) "
                               "does not exist in the system") %\
                               {'alias': reporter_alias})
            return True

        return self.join_reporter(message, reporter, clinic_code, role_code)

    def join_reporter(self, message, reporter, clinic_code, role_code):
        ''' sets a location and role for a reporter and mark him active '''

        # check clinic code
        try:
            clinic = HealthUnit.objects.get(code=clinic_code.lower())
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity,
                _(u"Subscribe error. Provided clinic code (%(clinic)s) "
                   "is wrong.") % {'clinic': clinic_code})
            return True

        # set location
        reporter.location = clinic.location_ptr

        # check role code
        try:
            role = Role.objects.get(code=role_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity,
                            _(u"Join Error. Provided Role code (%(role)s) "
                               "is wrong.") % {'role': role_code})
            return True

        reporter.role = role

        # set account active
        # /!\ we use registered_self as active
        reporter.registered_self = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity,
                        _(u"Success. You are now registered as %(role)s at "
                           "%(clinic)s with alias @%(alias)s.") %
                           {'clinic': clinic,
                            'role': reporter.role,
                            'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond(_(u"Success. %(reporter)s is now registered as "
                               "%(role)s at %(clinic)s with "
                               "alias @%(alias)s.") %
                               {'reporter': reporter,
                                'clinic': clinic,
                                'role': reporter.role,
                                'alias': reporter.alias})
        return True

    # STOP
    keyword.prefix = ["stop", "pause"]

    @keyword.blank()
    @registered
    def stop_registered(self, message):
        ''' Disables the sender in the system '''

        reporter = message.persistant_connection.reporter

        return self.stop_reporter(message, reporter)

    # STOP (ADMIN)
    keyword.prefix = ["stop", "pause"]

    @keyword(r'\@(slug)')
    @registered
    @admin
    def stop_admin(self, message, reporter_alias):
        ''' Disables an arbitrary reporter in the system '''

        try:
            reporter = Reporter.objects.get(alias=reporter_alias)
        except models.ObjectDoesNotExist:
            message.respond(_(u"Stop Error. The provided alias (%(alias)s) "
                               "does not exist in the system") %
                               {'alias': reporter_alias})
            return True

        return self.stop_reporter(message, reporter)

    def stop_reporter(self, message, reporter):
        ''' mark a reporter innactive in the system '''

        if not reporter.registered_self:
            message.respond(_(u"%(reporter)s is already inactive.") %
                               {'reporter': reporter})
            return True

        # set account inactive
        # /!\ we use registered_self as active
        reporter.registered_self = False

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity,
                        _(u"Success. You are now out of the system. Come "
                           "back by sending BACK."))

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond(_(u"Success. %(reporter)s is now out of "
                               "the system.") % {'reporter': reporter})
        return True

    # BACK
    keyword.prefix = ["back", "resume"]

    @keyword.blank()
    @registered
    def back(self, message):
        ''' Enables again the sender in the system '''

        reporter = message.persistant_connection.reporter

        return self.back_reporter(message, reporter)

    # BACK (ADMIN)
    keyword.prefix = ["back", "resume"]

    @keyword(r'\@(slug)')
    @registered
    @admin
    def back_one(self, message, reporter_alias):
        ''' Enables again an arbitrary reporter in the system '''

        try:
            reporter = Reporter.objects.get(alias=reporter_alias)
        except models.ObjectDoesNotExist:
            message.respond(_(u"Stop Error. The provided alias (%(alias)s) "
                               "does not exist in the system") %
                               {'alias': reporter_alias})
            return True

        return self.back_reporter(message, reporter)

    def back_reporter(self, message, reporter):
        ''' mark a reporter active in the system '''

        if reporter.registered_self:
            message.respond(_(u"%(reporter)s is already active.") %
                               {'reporter': reporter})
            return True

        # set account inactive
        # /!\ we use registered_self as active
        reporter.registered_self = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity,
                        _(u"Success. You are back in the system with alias "
                           "%(alias)s.") % {'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond(_(u"Success. %(reporter)s is back as %(role)s "
                               "at %(clinic)s.") %
                               {'reporter': reporter,
                                'clinic': reporter.location,
                                'role': reporter.role})
        return True

    # LOOKUP
    keyword.prefix = ["lookup", "search"]

    @keyword(r'(letters)\s?(\w*)')
    @registered
    def back(self, message, clinic_code, name):
        ''' List reporters from a location matching a name '''

        # check clinic code
        try:
            clinic = Location.objects.get(code=clinic_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity,
                            _(u"Lookup Error. Provided Clinic code "
                               "(%(clinic)s) is wrong.") %
                               {'clinic': clinic_code})
            return True

        # get list of reporters
        reporters = Reporter.objects.filter(location=clinic,
                                              registered_self=True)

        if name != None and name.__len__() > 0:
            reporters = reporters.filter(first_name__contains=name)

        if reporters.__len__() == 0:
            message.respond(_(u"No such people at %(clinic)s.") %
                               {'clinic': clinic})
            return True

        msg = ""
        msg_stub = _(u"%(reporter)s/%(alias)s is %(role)s at "
                      "%(clinic)s with %(number)s")

        # construct answer
        for areporter in reporters:
            mst = msg_stub % {'reporter': areporter, 'alias': areporter.alias,
                              'role': areporter.role.code.upper(),
                              'clinic': areporter.location.code.upper(),
                              'number': areporter.connection().identity}
            if msg.__len__() == 0:
                msg = mst
            else:
                msg = _(u"%s, %s") % (msg, mst)

        # strip long list
        if msg.__len__() >= 160:
            intro = _("%(nb)s results. ") % {'nb': reporters.__len__()}
            msg = intro + msg[: - intro.__len__()]

        # answer
        message.respond(msg)

        return True

    ############################
    #  DISEASES REPORTING (1/4)
    ############################

    keyword.prefix = ""

    @keyword(r'report(\-[0-9])? (.*)')
    @registered
    def diseases_report(self, message, period, text):

        # reporter
        reporter = message.persistant_connection.reporter

        # period
        period = 0 if not period else int(period[1:])
        try:
            report_week = ReportPeriod.from_index(period)
        except ErroneousDate:
            message.respond(_(u"FAILED. Sorry, no reports are allowed "
                               "on Sundays. Retry tomorrow."))
            return True

        try:
            diseases = diseases_from_string(text)
        except InvalidInput:
            message.respond(_(u"FAILED. Sorry, the format of your report "
                               "could not be understood. Please check syntax "
                               "and try again."))
            return True
        except IncoherentValue, e:
            message.respond(e.message)
            return True

        # create report object
        if DiseasesReport.objects.filter(reporter=reporter,
                                         period=period).count() > 0:
            pass

        report = DiseasesReport.by_reporter_period(reporter=reporter,
                                                    period=report_week)
        report.reset()

        # grab all diseases and assume 0 for undeclared
        try:
            all_diseases = list(Disease.objects.all())
            for dis in diseases:
                obs = DiseaseObservation.by_values(disease=dis['disease'],
                                                   cases=dis['cases'],
                                                   deaths=dis['deaths'])
                report.diseases.add(obs)
                try:
                    all_diseases.remove(dis['disease'])
                except:
                    raise IncoherentValue
            for dis in all_diseases:
                if dis in diseases:
                    continue
                obs = DiseaseObservation.by_values(disease=dis,
                                                   cases=0, deaths=0)
                report.diseases.add(obs)

            # save diseases
            report.save()
        except IncoherentValue, e:
            message.respond(e.message)
            return True

        # Disease threshold search
        locations = reporter.location.ancestors(include_self=True)
        alerts = []
        for disease in diseases:
            print disease
            triggers = DiseaseAlertTrigger.objects.filter(
                                                disease=disease['disease'],
                                                location__in=locations)
            for trigger in triggers:
                print trigger
                alert = trigger.raise_alert(period=report_week,
                                            location=reporter.location)
                if alert:
                    alerts.append(alert)

        # Add to Master Report
        master_report = EpidemiologicalReport.by_clinic_period(
                            clinic=HealthUnit.by_location(reporter.location),
                            period=report_week)

        master_report.diseases = report
        master_report.save()

        message.respond(_(u"%(comp)s Thank you for %(date)s %(title)s! "
                           "%(summary)s") %
                           {'date': report.period, 'title': report.title,
                            'comp': master_report.quarters,
                            'summary': report.summary})

        self.completed_report(message, master_report)
        return True

    ################################
    #  MALARIA CASES REPORTING (2/4)
    ################################

    keyword.prefix = ""

    @keyword(r'test(\-[0-9])? (numbers) (numbers) (numbers) (numbers) '
                             '(numbers) (numbers) (numbers) (numbers)')
    @registered
    def malaria_cases_report(self, message, period, opd_attendance,
                             suspected_cases, rdt_tests, rdt_positive_tests,
                             microscopy_tests, microscopy_positive,
                             positive_under_five, positive_over_five):

        # reporter
        reporter = message.persistant_connection.reporter

        # period
        period = 0 if not period else int(period[1:])
        try:
            report_week = ReportPeriod.from_index(period)
        except ErroneousDate:
            message.respond(_(u"FAILED. Sorry, no reports are allowed on "
                               "Sundays. Retry tomorrow."))
            return True

        # input verification
        try:
            opd_attendance = int(opd_attendance)
            suspected_cases = int(suspected_cases)
            rdt_tests = int(rdt_tests)
            rdt_positive_tests = int(rdt_positive_tests)
            microscopy_tests = int(microscopy_tests)
            microscopy_positive = int(microscopy_positive)
            positive_under_five = int(positive_under_five)
            positive_over_five = int(positive_over_five)
        except:
            message.respond(_(u"FAILED. Sorry, the format of your report "
                               "could not be understood. Please check "
                               "syntax and try again."))
            return True

        # create report object
        if MalariaCasesReport.objects.filter(reporter=reporter,
                                             period=period).count() > 0:
            pass

        report = MalariaCasesReport.by_reporter_period(reporter=reporter,
                                                       period=report_week)
        report.reset()

        try:
            report.update(opd_attendance=opd_attendance,
                          suspected_cases=suspected_cases,
                          rdt_tests=rdt_tests,
                          rdt_positive_tests=rdt_positive_tests,
                          microscopy_tests=microscopy_tests,
                          microscopy_positive=microscopy_positive,
                          positive_under_five=positive_under_five,
                          positive_over_five=positive_over_five)
        except IncoherentValue, e:
            message.respond(e.message)
            return True

        # Add to Master Report
        master_report = EpidemiologicalReport.by_clinic_period(
                            clinic=HealthUnit.by_location(reporter.location),
                            period=report_week)
        master_report.malaria_cases = report
        master_report.save()

        message.respond(_(u"%(comp)s Thank you for %(date)s %(title)s! "
                           "%(summary)s") %
                           {'date': report.period,
                            'title': report.title,
                            'comp': master_report.quarters,
                            'summary': report.summary})

        self.completed_report(message, master_report)
        return True

    #####################################
    #  MALARIA TREATMENTS REPORTING (3/4)
    #####################################

    keyword.prefix = ""

    @keyword(r'treat(\-[0-9])? (numbers) (numbers) (numbers) '
                              '(numbers) (numbers) (numbers)')
    @registered
    def malaria_treatments_report(self, message, period, rdt_negative,
                                  rdt_positive, four_months_to_three,
                                  three_to_seven, seven_to_twelve,
                                  twelve_and_above):

        # reporter
        reporter = message.persistant_connection.reporter

        # period
        period = 0 if not period else int(period[1:])
        try:
            report_week = ReportPeriod.from_index(period)
        except ErroneousDate:
            message.respond(_(u"FAILED. Sorry, no reports are allowed on "
                               "Sundays. Retry tomorrow."))
            return True

        # input verification
        try:
            rdt_negative = int(rdt_negative)
            rdt_positive = int(rdt_positive)
            four_months_to_three = int(four_months_to_three)
            three_to_seven = int(three_to_seven)
            seven_to_twelve = int(seven_to_twelve)
            twelve_and_above = int(twelve_and_above)

        except:
            message.respond(_(u"FAILED. Sorry, the format of your report "
                               "could not be understood. Please check "
                               "syntax and try again."))
            return True

        # create report object
        if MalariaTreatmentsReport.objects.filter(reporter=reporter,
                                                  period=period).count() > 0:
            pass

        report = MalariaTreatmentsReport.by_reporter_period(reporter=reporter,
                                                            period=report_week)
        report.reset()

        try:
            report.update(rdt_negative=rdt_negative, rdt_positive=rdt_positive,
                          four_months_to_three=four_months_to_three,
                          three_to_seven=three_to_seven,
                          seven_to_twelve=seven_to_twelve,
                          twelve_and_above=twelve_and_above)
        except IncoherentValue, e:
            message.respond(e.message)
            return True

        # Add to Master Report
        master_report = EpidemiologicalReport.by_clinic_period(
                            clinic=HealthUnit.by_location(reporter.location),
                            period=report_week)
        master_report.malaria_treatments = report
        master_report.save()

        message.respond(_(u"%(comp)s Thank you for %(date)s %(title)s! "
                           "%(summary)s") %
                          {'date': report.period, 'title': report.title,
                           'comp': master_report.quarters,
                           'summary': report.summary})

        self.completed_report(message, master_report)
        return True

    ##################################
    #  ACT CONSUMPTION REPORTING (4/4)
    ##################################

    keyword.prefix = ""

    @keyword(r'act(\-[0-9])? (numbers) (numbers) (numbers) (numbers) '
                            '(numbers) (numbers) (numbers) (numbers) '
                            '(numbers) (numbers)')
    @registered
    def act_consumption_report(self, message, period, yellow_dispensed,
                               yellow_balance, blue_dispensed, blue_balance,
                               brown_dispensed, brown_balance, green_dispensed,
                               green_balance, other_act_dispensed,
                               other_act_balance):

        # reporter
        reporter = message.persistant_connection.reporter

        # period
        period = 0 if not period else int(period[1:])
        try:
            report_week = ReportPeriod.from_index(period)
        except ErroneousDate:
            message.respond(_(u"FAILED. Sorry, no reports are allowed on "
                               "Sundays. Retry tomorrow."))
            return True

        # input verification
        try:
            yellow_dispensed = int(yellow_dispensed)
            yellow_balance = int(yellow_balance)
            blue_dispensed = int(blue_dispensed)
            blue_balance = int(blue_balance)
            brown_dispensed = int(brown_dispensed)
            brown_balance = int(brown_balance)
            green_dispensed = int(green_dispensed)
            green_balance = int(green_balance)
            other_act_dispensed = int(other_act_dispensed)
            other_act_balance = int(other_act_balance)
        except:
            raise
            message.respond(_(u"FAILED. Sorry, the format of your report "
                               "could not be understood. Please check syntax "
                               "and try again."))
            return True

        # create report object
        if ACTConsumptionReport.objects.filter(reporter=reporter,
                                               period=period).count() > 0:
            pass

        report = ACTConsumptionReport.by_reporter_period(reporter=reporter,
                                                          period=report_week)
        report.reset()

        try:
            report.update(yellow_dispensed=yellow_dispensed,
                          yellow_balance=yellow_balance,
                          blue_dispensed=blue_dispensed,
                          blue_balance=blue_balance,
                          brown_dispensed=brown_dispensed,
                          brown_balance=brown_balance,
                          green_dispensed=green_dispensed,
                          green_balance=green_balance,
                          other_act_dispensed=other_act_dispensed,
                          other_act_balance=other_act_balance)
        except IncoherentValue, e:
            message.respond(e.message)
            return True

        # Add to Master Report
        master_report = EpidemiologicalReport.by_clinic_period(
                              clinic=HealthUnit.by_location(reporter.location),
                              period=report_week)
        master_report.act_consumption = report
        master_report.save()

        message.respond(_(u"%(comp)s Thank you for %(date)s %(title)s! "
                           "%(summary)s") %
                          {'date': report.period, 'title': report.title,
                           'comp': master_report.quarters,
                           'summary': report.summary})

        self.completed_report(message, master_report)
        return True

    ####################
    #  REMARKS REPORTING
    ####################

    keyword.prefix = ""

    @keyword(r'remarks(\-[0-9])? (.+)')
    @registered
    def remarks_report(self, message, period, text):

        # reporter
        reporter = message.persistant_connection.reporter

        # period
        period = 0 if not period else int(period[1:])
        try:
            report_week = ReportPeriod.from_index(period)
        except ErroneousDate:
            message.respond(_(u"FAILED. Sorry, no reports are allowed on "
                               "Sundays. Retry tomorrow."))
            return True

        # Add to Master Report
        master_report = EpidemiologicalReport.by_clinic_period(
                            clinic=HealthUnit.by_location(reporter.location),
                            period=report_week)
        master_report.remarks = text[:160]
        master_report.save()

        message.respond(_(u"%(comp)s Thank you for adding a comment to "
                           "%(date)s %(title)s!") %
                          {'date': master_report.period,
                           'title': master_report.title,
                           'comp': master_report.quarters})

        self.completed_report(message, master_report)
        return True

    ############################
    #  COMPLETED REPORT FEEDBACK
    ############################

    def completed_report(self, message, report):

        if report.complete and not report.completed:

            report.completed_on = datetime.now()
            report.status = report.STATUS_COMPLETED
            report.save()

            message.respond(_(u"Thank you for completing %(date)s %(title)s! "
                               "Your receipt number is %(receipt)s") %
                              {'date': report.period, 'title': report.title,
                               'receipt': report.receipt})

        # send notification
        report_completed_alerts(self.router, report)

        return True

    ############################
    #  STATUS OF REPORT FEEDBACK
    ############################

    keyword.prefix = ""

    @keyword(r'progress(\-[0-9])?')
    @registered
    def report_status(self, message, period):

        # reporter
        reporter = message.persistant_connection.reporter

        # period
        period = 0 if not period else int(period[1:])
        try:
            report_week = ReportPeriod.from_index(period)
        except ErroneousDate:
            message.respond(_(u"FAILED. Sorry, no reports are allowed on "
                               "Sundays. Retry tomorrow."))
            return True

        # Get Master Report
        try:
            report = EpidemiologicalReport.objects.get(
                            clinic=HealthUnit.by_location(reporter.location),
                            period=report_week)
        except EpidemiologicalReport.DoesNotExist:
            message.respond(_(u"I am sorry but there is no such report for "
                               "%(date)s yet.") % {'date': report_week})
            return True

        message.respond(_(u"%(status)s %(date)s %(title)s! %(summary)s") %
                          {'date': report.period,
                           'status': report.verbose_status,
                           'title': report.title, 'summary': report.summary})
        return True
