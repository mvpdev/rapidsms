#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga, rgaudin

from django.utils.translation import gettext as _

from django.db.models import F
from django.db.models import Avg, Count, Sum

import calendar
from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from childcount.models import Patient
from locations.models import Location
from childcount.models import CHW, Clinic
from childcount.models import NutritionReport
from childcount.models import StillbirthMiscarriageReport
from childcount.models import MedicineGivenReport
from childcount.models import DangerSignsReport
from childcount.models import NeonatalReport
from childcount.models import FamilyPlanningReport
from childcount.models import FeverReport
from childcount.models import CodedItem
from childcount.models import ReferralReport
from childcount.models import BirthReport
from childcount.models import PregnancyReport, SPregnancy
from childcount.models import HouseholdVisitReport
from childcount.models import FollowUpReport
from childcount.models import ImmunizationSchedule
from childcount.models import ImmunizationNotification
from childcount.models import BedNetReport
from childcount.models import BednetIssuedReport
from childcount.models import BednetUtilization
from childcount.models import DrinkingWaterReport
from childcount.models import SanitationReport
from childcount.models import AppointmentReport
from childcount.models import UnderOneReport
from childcount.models import DeathReport

from childcount.utils import day_end, \
                                day_start, \
                                get_dates_of_the_week, \
                                get_median, \
                                seven_days_to_date, \
                                first_day_of_month, \
                                last_day_of_month, \
                                first_date_of_week
from childcount.reports.indicator import Indicator, INDICATOR_EMPTY
from childcount.reports.utils import MonthlyPeriodSet

from logger.models import IncomingMessage, OutgoingMessage


class ThePatient(Patient):

    class Meta:
        verbose_name = _("Patient List Report")
        proxy = True

    def latest_muac_raw(self):
        try:
            n = NutritionReport\
                .objects\
                .filter(encounter__patient=self, \
                    muac__isnull=False,
                    muac__gt=0).latest()
        except NutritionReport.DoesNotExist:
            return None
        return n

    def latest_muac_date(self):
        n = self.latest_muac_raw()
        if n is None:
            return _(u"[No MUAC]")
        
        ''' Oed = Oedema '''
        return _(u"%(date)s [%(muac)s,Oed:%(oedema)s]") % \
            {'date': n.encounter.encounter_date.strftime('%d %b %Y'),
            'muac': n.muac or '--',
            'oedema': n.oedema}

    def latest_muac(self):
        muac = self.latest_muac_raw()
        if muac is not None:
            return u"%smm %s" % (muac.muac, muac.verbose_state)
        return u""

    def check_visit_within_seven_days_of_birth(self):
        seven_days_after_birth = self.dob + timedelta(8)
        hvr = HouseholdVisitReport.objects\
                .filter(encounter__encounter_date__gt=self.dob, \
                    encounter__encounter_date__lte=seven_days_after_birth, \
                    encounter__patient=self.household)\
                .count()

        nn = NeonatalReport\
            .objects\
            .filter(encounter__encounter_date__gt=self.dob, \
                encounter__encounter_date__lte=seven_days_after_birth, \
                encounter__patient=self)\
            .count()

        return hvr + nn

    def visit_within_90_days_of_last_visit(self, relative_to=date.today()):
        try:
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household,\
                            encounter__encounter_date__lte=relative_to).latest()
            latest_date = hvr.encounter.encounter_date
            old_date = latest_date - timedelta(90)
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household, \
                                encounter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if hvr.count():
                return True
            return False
        except HouseholdVisitReport.DoesNotExist:
            return False

    def latest_imm_report(self, relative_to=date.today()):
        try:
            ir = UnderOneReport\
                    .objects\
                    .filter(encounter__patient=self, \
                        encounter__encounter_date__lte=relative_to)\
                    .latest()
        except UnderOneReport.DoesNotExist:
            return None

        return ir

    def is_immunized(self, relative_to=date.today()):
        try:
            ir = UnderOneReport\
                    .objects\
                    .filter(encounter__patient=self, \
                        encounter__encounter_date__lte=relative_to,\
                        immunized=UnderOneReport.IMMUNIZED_YES)
        except UnderOneReport.DoesNotExist:
            return False

        return (ir.count() > 0)


    def ontime_muac(self, relative_to=date.today()):
        # MUAC should be every 3 months for healthy kids
        # and every 1 month for kids with SAM/MAM

        # Get the most recent NutritionReport
        try:
            nr = NutritionReport\
                    .objects\
                    .filter(encounter__patient=self, \
                        encounter__encounter_date__lte=relative_to)\
                    .latest('encounter__encounter_date')
        except NutritionReport.DoesNotExist:
            return False

        days_old = (relative_to - nr.encounter.encounter_date.date()).days

        # First, check if the current MUAC is out of date
        if nr.status == NutritionReport.STATUS_HEALTHY:
            if days_old > 90:
                return False
        else:
            if days_old > 30:
                return False

        return True
        
        '''
        # Next, get the previous MUAC
        latest_date = nr.encounter.encounter_date.date()

        # If a month before the child's last MUAC, the child was
        # under 6 months old, then growth monitoring is okay
        if (latest_date - timedelta(30)) < (self.dob + timedelta(182)):
            return True

        # Otherwise, make sure that there was a previous MUAC
        try:
            secnr = NutritionReport\
                .objects\
                .filter(encounter__patient=self, \
                        encounter__encounter_date__lt=latest_date)\
                .latest('encounter__encounter_date')
        except NutritionReport.DoesNotExist:
            # If there's no previous MUAC
            return False

        # Check that the first report is timely relative to 
        # MUAC guidelines
        days_diff = (latest_date - \
            secnr.encounter.encounter_date.date()).days
        if secnr.status == NutritionReport.STATUS_HEALTHY:
            if days_diff > 90: return False
        else:
            if days_diff > 30: return False
        '''

    def status_text(self):
        ''' Return the text in status choices '''
        if not self.pk:
            return ''
        #TODO There is a smarter way of doing this, get it done
        for status in self.STATUS_CHOICES:
            if self.status in status:
                return status[1]
        return ''

    def generate_schedule(self):
        'Generate immunization '
        schedule = ImmunizationSchedule.objects.all()
        for period in schedule:
            patient_dob = self.dob
            notify_on = datetime.today()
            immunization = ImmunizationNotification()
            if not ImmunizationNotification.objects.filter(patient=self, \
                                                        immunization=period):
                immunization.patient = self
                immunization.immunization = period
                if period.period_type == ImmunizationSchedule.PERIOD_DAYS:
                    notify_on = patient_dob + timedelta(period.period)
                    immunization.notify_on = notify_on
                if period.period_type == ImmunizationSchedule.PERIOD_WEEKS:
                    notify_on = patient_dob + timedelta(period.period * 7)
                    immunization.notify_on = notify_on
                if period.period_type == ImmunizationSchedule.PERIOD_MONTHS:
                    notifyon = patient_dob + timedelta(30.4375 * period.period)
                    immunization.notify_on = notifyon

                immunization.save()

    def survey(self):
        #Get aggregate of bednets survey questions per chw
        survey = []
        try:
            bednet = BedNetReport.objects.get(encounter__patient=self)
            survey = ({'damaged': bednet.damaged_nets,
                       'function': bednet.function_nets,
                       'num_site': bednet.sleeping_sites,
                       'earlier': bednet.earlier_nets})
        except:
            pass

        #Get sanitation report
        try:
            san = SanitationReport.objects.get(encounter__patient=self)
            survey.update({'toilet_type': san.toilet_lat})
            if san.share_toilet is SanitationReport.U:
                survey.update({'share': 'U'})
            elif san.share_toilet is SanitationReport.PB:
                survey.update({'share': 'PB'})
            else:
                survey.update({'share': san.share_toilet})
        except:
            pass

        #Get drinking water report
        try:
            dwr = DrinkingWaterReport.objects.get(encounter__patient=self)
            survey.update({'water_source': dwr.water_source,
                           'treat_method': dwr.treatment_method})
        except:
            pass

        #get bednet utilization
        try:
            bedutil = BednetUtilization.objects.get(encounter__patient=self)
            survey.update({'under_five': bedutil.child_underfive,
                           'slept_bednet': bedutil.child_lastnite,
                           'hanging': bedutil.hanging_bednet,
                           'reason': bedutil.reason})
        except:
            pass

        for item in survey:
            if survey[item] is None:
                survey[item] = '-'
        # issued 
        bdnt_issued = BednetIssuedReport.objects.filter(\
                                    encounter__patient=self)\
                                    .aggregate(\
                                    stotal=Sum('bednet_received'))['stotal']
        if not bdnt_issued:
            bdnt_issued = 0
        survey.update({'issued': bdnt_issued})
        return survey

    def required_bednet(self):
        bdnt_issued = BednetIssuedReport.objects.filter(\
                                    encounter__patient=self)\
                                    .aggregate(\
                                    stotal=Sum('bednet_received'))['stotal']
        try:
            total = self.survey()['num_site'] - self.survey()['function']
            if bdnt_issued:
                total -= bdnt_issued
            if total < 0:
                total = 0
        except:
            total = '-'

        return total

    def household_members(self):
        return ThePatient.objects.filter(household=self.household)

    def polio(self):
        from childcount.models.PolioCampaignReport import PolioCampaignReport
        from childcount.models import Configuration
        c = Configuration.objects.get(key='polio_round')
        try:
            pl = PolioCampaignReport.objects.get(patient=self, \
                phase=int(c.value))
        except PolioCampaignReport.DoesNotExist:
            return _(u"No")
        else:
            return _(u"Yes")

    @classmethod
    def under_five(cls, chw=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        if chw:
            p = cls.objects.filter(dob__gte=sixtym, \
                                       chw=chw).order_by("household")
        else:
            p = cls.objects.filter(dob__gte=sixtym).order_by("household")
        return p

    @classmethod
    def patients_summary_list(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('household').verbose_name.upper(), \
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('health_id').verbose_name.upper(), \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _("Name".upper()), \
            'bit': "{{object.last_name}}{% if object.pk %},{% endif %} "
                    "{{object.first_name}}"})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name.upper(), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _("Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _("Last MUAC".upper()), \
            'bit': '{{object.latest_muac}}'})
        columns.append(
            {'name': cls._meta.get_field('chw').verbose_name.upper(), \
            'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def underfive_summary_list(cls):
        columns = []
        columns.append(
            {'name': _("HID".upper()), \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _("Name".upper()), \
            'bit': '{{object.full_name}} {{object.gender}} / '
                    '{{object.humanised_age}}'})
        columns.append(
            {'name': _("Last MUAC".upper()), \
            'bit': '{{object.latest_muac}}'})
        columns.append(
            {'name': _("Polio".upper()), \
            'bit': '{{object.polio}}'})

        sub_columns = None
        return columns, sub_columns

    def patient_register_columns(cls):
        columns = []
        columns.append(
            {'name': _(u"LOC"), \
            'bit':
                '{% if object.is_head_of_household %}<strong>' \
                '{{ object.household.location.code }}' \
                '</strong>{% endif %}'})
        columns.append(
            {'name': _(u"HID"), \
            'bit':
                '{% if object.is_head_of_household %}<strong>{% endif %}' \
                '{{object.health_id.upper}}' \
                '{% if object.is_head_of_household %}</strong>{% endif %}'})
        columns.append(
            {'name': _(u"Name".upper()), \
            'bit': "{{object.last_name}}{% if object.pk %},{% endif %} "
                    "{{object.first_name}}"})
        columns.append(
            {'name': _(u"Gen."), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _(u"Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _(u"Status".upper()), \
            'bit': '{{object.status_text}}'})
        #columns.append(
        #    {'name': _(u"HHID".upper()), \
        #    'bit': '{{object.household.health_id.upper}}'})
        return columns

    @classmethod
    def bednet_summary(cls):
        columns = []
        columns.append(
            {'name': _("Household ".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': _("Household Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': _("No. Sleeping site".upper()),
             'bit': '{{object.survey.num_site}}'})
        columns.append(
            {'name': _("Functioning Bednet".upper()),
             'bit': '{{object.survey.function}}'})
        columns.append(
            {'name': _("Earlier Bednets".upper()),
             'bit': '{{object.survey.earlier}}'})
        columns.append(
            {'name': _("Damaged Bednet".upper()),
             'bit': '{{object.survey.damaged}}'})
        columns.append(
            {'name': _("Required Bednets".upper()),
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': _("#under five last night".upper()),
             'bit': '{{object.survey.under_five}}'})
        columns.append(
            {'name': _("#slept on Bednet".upper()),
             'bit': '{{object.survey.slept_bednet}}'})
        columns.append(
            {'name': _("Hanging Bednet".upper()),
             'bit': '{{object.survey.hanging}}'})
        columns.append(
            {'name': _("Reason ".upper()),
             'bit': '{{object.survey.reason}}'})
        columns.append(
            {'name': _("Primary Sanitation".upper()),
             'bit': '{{object.survey.toilet_type}}'})
        columns.append(
            {'name': _("Shared?".upper()),
             'bit': '{{object.survey.share}}'})
        columns.append(
            {'name': _("Primary source of water".upper()),
             'bit': '{{object.survey.water_source}}'})
        columns.append(
            {'name': _("Treatment Method ".upper()),
             'bit': '{{object.survey.treat_method}}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def bednet_summary_minimal(cls):
        columns = []
        columns.append(
            {'name': _("HH".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': _("HH Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': _("# SSs".upper()),
             'bit': '{{object.survey.num_site}}'})
        columns.append(
            {'name': _("# Func. Nets".upper()),
             'bit': '{{object.survey.function}}'})
        columns.append(
            {'name': _("# Elr. Nets".upper()),
             'bit': '{{object.survey.earlier}}'})
        columns.append(
            {'name': _("# Dmgd. Nets".upper()),
             'bit': '{{object.survey.damaged}}'})
        columns.append(
            {'name': _("# Rqrd. Nets".upper()),
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': _("# U5 LN".upper()),
             'bit': '{{object.survey.under_five}}'})
        columns.append(
            {'name': _("# Slept on Net".upper()),
             'bit': '{{object.survey.slept_bednet}}'})
        columns.append(
            {'name': _("# Hanging Nets".upper()),
             'bit': '{{object.survey.hanging}}'})
        columns.append(
            {'name': _("Reason".upper()),
             'bit': '{{object.survey.reason}}'})
        columns.append(
            {'name': _("Primary SAN".upper()),
             'bit': '{{object.survey.toilet_type}}'})
        columns.append(
            {'name': _("Shared?".upper()),
             'bit': '{{object.survey.share}}'})
        columns.append(
            {'name': _("P. Water Source".upper()),
             'bit': '{{object.survey.water_source}}'})
        columns.append(
            {'name': _("Treatment".upper()),
             'bit': '{{object.survey.treat_method}}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def bednet_coverage(cls):
        columns = []
        columns.append(
            {'name': _("HH".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': _("HH Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': _("# SSs".upper()),
             'bit': '{{object.survey.num_site}}'})
        columns.append(
            {'name': _("# Func. Nets".upper()),
             'bit': '{{object.survey.function}}'})
        columns.append(
            {'name': _("# Elr. Nets".upper()),
             'bit': '{{object.survey.earlier}}'})
        columns.append(
            {'name': _("# Dmgd. Nets".upper()),
             'bit': '{{object.survey.damaged}}'})
        columns.append(
            {'name': _("# Nets Issued".upper()),
             'bit': '{{object.survey.issued}}'})
        columns.append(
            {'name': _("# Rqrd. Nets".upper()),
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': _("# U5 LN".upper()),
             'bit': '{{object.survey.under_five}}'})
        columns.append(
            {'name': _("# Slept on Net".upper()),
             'bit': '{{object.survey.slept_bednet}}'})
        columns.append(
            {'name': _("# Hanging Nets".upper()),
             'bit': '{{object.survey.hanging}}'})
        columns.append(
            {'name': _("Reason".upper()),
             'bit': '{{object.survey.reason}}'})
        sub_columns = None
        return columns, sub_columns

    @classmethod
    def mini_bednet_coverage(cls):
        columns = []
        columns.append(
            {'name': _("HH".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location.name }}'})
        columns.append(
            {'name': _("HH Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': _("# SSs".upper()),
             'bit': '{{object.survey.num_site}}'})
        columns.append(
            {'name': _("# Func. Nets".upper()),
             'bit': '{{object.survey.function}}'})
        columns.append(
            {'name': _("# Elr. Nets".upper()),
             'bit': '{{object.survey.earlier}}'})
        columns.append(
            {'name': _("# Dmgd. Nets".upper()),
             'bit': '{{object.survey.damaged}}'})
        columns.append(
            {'name': _("# Nets Issued".upper()),
             'bit': '{{object.survey.issued}}'})
        columns.append(
            {'name': _("# Rqrd. Nets".upper()),
             'bit': '{{object.required_bednet}}'})
        sub_columns = None
        return columns, sub_columns

class TheCHWReport(CHW):
    class Meta:
        verbose_name = _("Community Health Worker Report")
        proxy = True

    @property
    def mobile_phone(self):
        return self.connection().identity

    @property
    def num_of_patients(self):
        num = Patient.objects.filter(chw=self, \
                            status=Patient.STATUS_ACTIVE).count()
        return num

    @property
    def num_of_underfive(self):
        return self.patients_under_five().count()

    def patients_under_five(self, today = date.today()):
        sixtym = today - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(chw=self, \
                            dob__gte=sixtym, \
                            dob__lte=today,
                            status=Patient.STATUS_ACTIVE)

    @property
    def num_of_under_nine(self):
        return self.patients_under_nine().count()

    def patients_under_nine(self):
        ninem = date.today() - timedelta(int(30.4375 * 9))
        return Patient.objects.filter(chw=self, dob__gte=ninem, \
                            status=Patient.STATUS_ACTIVE)

    def patients_underone(self):
        oney = date.today() - timedelta(int(30.4375 * 12))
        return Patient.objects.filter(chw=self, dob__gte=oney, \
                            status=Patient.STATUS_ACTIVE)
    
    @property
    def num_of_sam(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            status=NutritionReport.STATUS_SEVERE_COMP).count()
        num += NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_SEVERE).count()
        return num

    @property
    def num_of_mam(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                status=NutritionReport.STATUS_MODERATE).count()
        return num

    def mam_cases(self, startDate=None, endDate=None):
        return NutritionReport.objects.filter(encounter__chw=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def severe_mam_cases(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(encounter__chw=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(encounter__chw=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        return num

    @property
    def num_of_healthy(self):
        num = NutritionReport.objects.filter(created_by=self, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                                status=NutritionReport.STATUS_HEALTHY).count()
        return num

    @property
    def num_of_visits(self):
        num = HouseholdVisitReport.objects.filter(created_by=self).count()
        return num

    def two_weeks_visits(self):
        two_weeks = datetime.now() + \
            relativedelta(weekday=calendar.MONDAY, days=-13)
        two_weeks = datetime.combine(two_weeks.date(), time(0, 0))
        return HouseholdVisitReport.objects.filter(encounter__chw=self, \
                            encounter__encounter_date__gte=two_weeks)\
                            .count()

    @property
    def num_muac_eligible(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(chw=self, dob__gte=sixtym, \
                                    status=Patient.STATUS_ACTIVE, \
                                    dob__lte=sixm).count()
        return num

    @classmethod
    def total_muac_eligible(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(dob__gte=sixtym, \
                                    status=Patient.STATUS_ACTIVE, \
                                     dob__lte=sixm).count()
        return num

    @property
    def num_of_sms(self):
        identity = self.connection().identity
        num = IncomingMessage.objects.filter(identity=identity).count()
        return num

    @property
    def number_of_households(self, today=None):
        return self.households(today).count()

    def households(self, today=None):
        '''
        List of households belonging to this CHW
        '''
        p = Patient.objects.filter(health_id=F('household__health_id'), \
                                        chw=self, status=Patient.STATUS_ACTIVE)
        if today is None:
            return p
        else:
            return p.filter(created_on__lte=today)

    def muac_list(self):
        '''
        List of patients in the muac age bracket
            - 6 months >= patient.age < 60 months
        '''
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        patients = Patient.objects.filter(chw=self, \
                                     dob__gte=sixtym, \
                                     dob__lte=sixm, \
                                     status=Patient.STATUS_ACTIVE)
        return patients

    def num_of_householdvisits(self):
        return HouseholdVisitReport.objects.filter(encounter__chw=self).count()

    def num_of_householdvisits_90_days(self):
        today = datetime.today().date()
        return self.household_visit(today - timedelta(90), today)

    def num_of_uniq_householdvisits_90_days(self):
        today = datetime.today().date()
        return self._household_visit(today - timedelta(90), today)\
            .values('household__health_id')\
            .distinct()\
            .count()
    
    def household_visit(self, startDate=None, endDate=None):
        return self._household_visit(startDate, endDate).count()
    
    def _household_visit(self, startDate=None, endDate=None):
        return HouseholdVisitReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)

    def household_visits_for_month(self, offset=0):
        # This list comprehension deserves some explanation.
        # First, we get a list of days from 30+offset days ago up
        # to today.
        # Then, we get (day, count) tuples for each of those
        # days, where count contains the number of
        # HH visits for that day by this CHW
        return [(i, self.household_visit(date.today() + timedelta(i), \
            date.today() + timedelta(i + 1))) \
                for i in xrange(-30 - offset, -offset)]

    def percentage_ontime_visits(self):
        (num_on_time, total_households) = \
            self._percentage_ontime_visits_raw()
        if total_households == 0:
            return None
        if num_on_time is 0:
            return 0
        else:
            return int(100.0 * num_on_time / float(total_households))

    def _percentage_ontime_visits_raw(self, relative_to=date.today()):
        households = self.households()
        num_on_time = 0
        for household in households:
            thepatient = ThePatient.objects.get(health_id=household.health_id)
            if thepatient.visit_within_90_days_of_last_visit(relative_to):
                num_on_time += 1
        return (num_on_time, households.count())

    def num_of_births(self):
        return BirthReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_birth_visits(self):
        births = BirthReport.objects.filter(encounter__chw=self)
        v_count = 0
        b_count = births.count()
        for birth in births:
            thepatient = ThePatient.objects.get(pk=birth.encounter.patient.pk)
            if thepatient.check_visit_within_seven_days_of_birth():
                v_count += 1
        print (v_count, b_count)
        if b_count == 0:
            return None
        elif v_count == 0:
            return 0
        else:
            return int(100.0 * v_count / float(b_count))

    def num_of_clinic_delivery(self):
        return BirthReport.objects.filter(encounter__chw=self, \
                    clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def percentage_clinic_deliveries(self):
        num_of_clinic_delivery = self.num_of_clinic_delivery()
        num_of_births = self.num_of_births()
        if num_of_births == 0:
            return None
        else:
            return int(100.0 * num_of_clinic_delivery / float(num_of_births))

    def num_underfive_refferred(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        rr = ReferralReport.objects.filter(encounter__patient__dob__lte=sixtym,
                        encounter__chw=self)
        return rr.count()

    def num_underfive_malaria(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        fr = FeverReport.objects.filter(encounter__patient__dob__lte=sixtym, \
                                        encounter__chw=self)
        return fr.count()

    def rdt_cases(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_underfive_diarrhea(self):
        #TODO
        return 0

    def percentage_ontime_muac(self):
        (num, den) = self.fraction_ontime_muac()

        if den == 0:
            return None

        if num == 0:
            return 0
        else:
            return int(round(100 * (num/ float(den))))

    def fraction_ontime_muac(self, relativeTo=date.today()):
        # Consider only kids over 6 months
        underfives = self.patients_under_five(relativeTo)
        underfives.filter(dob__lte=(relativeTo-timedelta(180)))

        count = 0
        for achild in underfives:
            thepatient = ThePatient.objects.get(id=achild.id)
            if thepatient.ontime_muac(relativeTo):
                count += 1

        return (count, underfives.count())

    def num_of_active_sam_cases(self, today=date.today()):
        count = 0
        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        nr = NutritionReport.objects\
                        .filter(encounter__chw=self, status__in=danger,\
                        encounter__encounter_date__lte=today)\
                        .values('encounter__patient').distinct()
        for r in nr:
            p = Patient.objects.get(id=r['encounter__patient'])
            latest = NutritionReport\
                .objects\
                .filter(encounter__patient=p,\
                    encounter__encounter_date__lte=today)\
                .latest()
            if latest.status in danger:
                count += 1
        return count

    def num_of_pregnant_women(self):
        return len(self.pregnant_women())

    def pregnant_women(self, today=datetime.today().date()):
        c = []
        # Need to use Sauri specific
        # Noticed that PregnancyReport.objects.filter(encounter__chw=self)
        # does returns [], with values('encounter__patient').distinct()
        # returns some values but they are different if SPregnancy is used
        if not PregnancyReport.objects.filter(encounter__chw=self):
            prgclass = SPregnancy
        else:
            prgclass = PregnancyReport
        pregs = prgclass\
            .objects\
            .filter(encounter__chw=self, \
                encounter__encounter_date__gt=today-timedelta(365.25),\
                encounter__encounter_date__lte=today)\
            .values('encounter__patient')\
            .distinct()
        print "got %d pregs" % pregs.count()

        for preg in pregs:
            patient = Patient.objects.get(pk=preg['encounter__patient'])
            pr = prgclass\
                .objects\
                .filter(encounter__patient=patient,\
                    encounter__encounter_date__lte=today,\
                    encounter__encounter_date__gt=today-timedelta(365.25))\
                .latest('encounter__encounter_date')

            # Number of days since encounter
            days = (today - pr.encounter.encounter_date.date()).days
            # Number of months since encounter
            months = round(days / 30.4375)

            print 'PR submitted %s at month %d (ago: %d)' % \
                (pr.encounter.encounter_date, pr.pregnancy_month, months)

            # If the pregnancy month plus months since encounter
            # is greater than 9 and there's no birth report,
            # then let's assume the lady is not pregnant
            months_pregnant = pr.pregnancy_month + months
            if months_pregnant > 9:
                print 'too old %d in %s' % \
                    (pr.pregnancy_month, pr.encounter.encounter_date)
                continue

            # Look for a baby since the pregnancy
            b = Patient\
                .objects\
                .filter(mother__pk=pr.encounter.patient.pk,\
                    dob__gte=today-timedelta(months_pregnant*30.4375),\
                    dob__lte=today)

            # If the birthreport has been found, then she's no longer
            # pregnant
            if b.count() > 0:
                print 'birth at %d' % months_pregnant
                continue

            # Look for a stillbirth/miscarriage
            s = StillbirthMiscarriageReport\
                .objects\
                .filter(encounter__patient__pk=pr.encounter.patient.pk,\
                    incident_date__gte=\
                        today-timedelta(months_pregnant*30.4375),\
                    incident_date__lte=today)

            # If there was a stillbirth/misscariage, then she's
            # no longer pregnant
            if s.count() > 0:
                print 'stillbirth'
                continue
            
            print '*PR submitted %s at month %d (ago: %d)' % \
                (pr.encounter.encounter_date, pr.pregnancy_month, months)
            c.append(patient)
        return c

    def num_pregnant_refferred(self):
        pwomen = self.pregnant_women()
        return ReferralReport\
            .objects\
            .filter(\
                encounter__patient__in=pwomen, \
                encounter__chw=self)\
            .exclude(urgency=ReferralReport.URGENCY_CONVENIENT).count()

    def percentage_pregnant_ontime_visits(self):
        pwomen = self.pregnant_women()

        if len(pwomen) == 0:
            return None

        # Check if report submitted was Sauri report or standard
        # report
        if not PregnancyReport.objects.filter(encounter__chw=self):
            prgclass = SPregnancy
        else:
            prgclass = PregnancyReport

        count = 0
        for patient in pwomen:
            pr = prgclass.objects.filter(encounter__patient=patient)\
                                        .latest('encounter__encounter_date')
            latest_date = pr.encounter.encounter_date
            old_date = latest_date - timedelta(6 * 7)
            pr = prgclass.objects.filter(encounter__patient=patient, \
                                encounter__encounter_date__gte=latest_date, \
                                encounter__encounter_date__lt=old_date)
            if pr.count():
                count += 1
        if not count:
            return count
        else:
            total_count = len(pwomen)
            return int(round(100 * (count / float(total_count))))

    def people_without_followup(self, start_date=date(1901,01,01),\
            end_date=date.today()):

        print (start_date, end_date)
        referrals = ReferralReport\
            .objects\
            .filter(encounter__chw=self, \
                encounter__encounter_date__lte=end_date,\
                encounter__encounter_date__gte=start_date)\
            .exclude(urgency=ReferralReport.URGENCY_CONVENIENT)

        num_referrals = referrals.count()
        if num_referrals == 0:
            print "No referrals"
            return None

        ontime = []
        nofup = []
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            day2later = day_end(rdate + timedelta(3))
            try:
                fur = FollowUpReport.objects.filter(encounter__chw=self, \
                            encounter__patient=referral.encounter.patient, \
                            encounter__encounter_date__gt=rdate, \
                            encounter__encounter_date__lte=day2later)
            except FollowUpReport.DoesNotExist:
                pass
                print "Ref: %s, FU: None" % rdate.date()

            if fur.count() > 0:
                print "Ref: %s, FU: %s" % (rdate.date(), \
                    fur[0].encounter.encounter_date.date())
                ontime.append(referral)
            else:
                nofup.append(referral)
                print "Ref: %s, FU: None" % rdate.date()

        return (ontime, nofup)

    def percentage_ontime_followup(self, start_date=date(1901,01,01),\
            end_date=date.today(), raw=False):

        out = self.people_without_followup(start_date, end_date)
        if out is None:
            return None

        (ontime, nofup) = out
        n_ontime = len(ontime)
        n_nofup = len(nofup)
        n_total = n_ontime + n_nofup

        if raw:
            return (n_ontime, n_total)
        else:
            return int(round((n_ontime/ \
                        float(n_total)) * 100))

    def median_number_of_followup_days(self):
        referrals = ReferralReport.objects.filter(encounter__chw=self)
        lsdays = []
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            fur = FollowUpReport.objects.filter(encounter__chw=self, \
                            encounter__patient=referral.encounter.patient, \
                            encounter__encounter_date__gt=rdate)\
                            .order_by('encounter__encounter_date')
            if fur:
                fdate = fur[0].encounter.encounter_date
                lsdays.append((fdate - rdate).days)
        if not lsdays:
            return ''
        return int(get_median(lsdays))

    def sms_error_rate(self):
        total_sms = IncomingMessage.objects.filter(identity=self.connection()\
                                    .identity).count()
        if total_sms == 0:
            return None
        total_error_sms = OutgoingMessage.objects.filter(identity=self\
                                    .connection().identity, \
                                    text__icontains='error').count()
        return int(round((total_error_sms / float(total_sms)) * 100))

    def days_since_last_sms(self):
        now = datetime.now()
        last_sms = IncomingMessage.objects.filter(identity=self.connection()\
                                    .identity, received__lte=now)\
                                    .order_by('-received')
        if not last_sms:
            return None
        return (now - last_sms[0].date).days

    def activity_summary(self):
        today = datetime.today()
        startDate = today - timedelta(today.weekday())
        p = {}

        p['sdate'] = startDate.strftime('%d %b')
        p['edate'] = today.strftime('%d %b')
        p['severemuac'] = self.severe_mam_cases(startDate=startDate, \
                            endDate=today)
        p['numhvisit'] = self.household_visit(startDate=startDate, \
                            endDate=today)
        p['muac'] = self.mam_cases(startDate=startDate, endDate=today)
        p['rdt'] = self.rdt_cases(startDate=startDate, endDate=today)
        p['household'] = self.number_of_households
        p['tclient'] = self.num_of_patients
        p['ufive'] = self.num_of_underfive
        p['unine'] = self.num_of_under_nine
        p['underone'] = self.patients_underone().count()

        return p

    def chw_activities_summary(self, startDate, endDate=datetime.today()):
        p = {}

        p['sdate'] = startDate.strftime('%d %b')
        p['edate'] = endDate.strftime('%d %b')
        p['severemuac'] = self.severe_mam_cases(startDate=startDate, \
                            endDate=endDate)
        p['numhvisit'] = self.household_visit(startDate=startDate, \
                            endDate=endDate)
        p['muac'] = self.mam_cases(startDate=startDate, endDate=endDate)
        p['rdt'] = self.rdt_cases(startDate=startDate, endDate=endDate)
        p['household'] = self.number_of_households
        p['tclient'] = self.num_of_patients
        p['ufive'] = self.num_of_underfive
        p['unine'] = self.num_of_under_nine
        p['underone'] = self.patients_underone().count()

        return p

    def num_of_bednetsurvey(self):
        return BedNetReport.objects.filter(encounter__chw=self).count()

    def per_bednetsurvey(self):
        #Percentage survey done
        num_survey = self.num_of_bednetsurvey()
        num_household = self.number_of_households
        if num_household > 0:
            ans = int(round((num_survey / float(num_household)) * 100))
        else:
            ans = 0
        return ans

    def bednet_survey(self):
        #Get aggregate of bednets survey questions per chw
        survey = BedNetReport.objects.filter(encounter__chw=self)\
                                     .aggregate(\
                                            total=Count('encounter'),
                                            damaged=Sum('damaged_nets'),
                                            function=Sum('function_nets'),
                                            num_site=Sum('sleeping_sites'),
                                            earlier=Sum('earlier_nets'))
        for item in survey:
            if survey[item] is None:
                survey[item] = '-'
        return survey

    def required_bednet(self):
        total = self.num_sleepingsite() - self.num_funcbednet()
        if total < 0:
            total = 0
        return total

    def num_sanitation(self):
        'total survey done  on sanitation'
        return SanitationReport.objects.filter(encounter__chw=self).count()

    def num_netutilization(self):
        'total survey done on bednet utilization'
        return BednetUtilization.objects.filter(encounter__chw=self).count()

    def num_drinkingwater(self):
        'total survey done on drinking water '
        return DrinkingWaterReport.objects.filter(encounter__chw=self).count()

    def current_monthly_appointments(self):
        '''AppointmentReports since the start of the month to date'''
        today = datetime.today().date()
        start_of_month = today - timedelta(today.day - 1)
        apts = AppointmentReport.objects.filter(encounter__chw=self,
                                appointment_date__gte=start_of_month,
                                appointment_date__lte=today)
        return apts

    def num_of_appointment(self):
        return self.current_monthly_appointments().count()

    def percentage_reminded(self):
        apts = self.current_monthly_appointments()
        total = apts.count()
        reminded = apts.filter(status__in=(AppointmentReport.STATUS_PENDING_CV,
                                            AppointmentReport.STATUS_CLOSED))
        if total == 0:
            return None
        return int(round((reminded.count() / float(total)) * 100, 0))

    def score(self):
        pov = pobv = pom = ppov = pr = pof = 0
        div_by = 0
        if self.percentage_ontime_visits():
            pov = self.percentage_ontime_visits()
            div_by += 1
        if self.percentage_ontime_birth_visits():
            pobv = self.percentage_ontime_birth_visits()
            div_by += 1
        if self.percentage_ontime_muac():
            pom = self.percentage_ontime_muac()
            div_by += 1
        if self.percentage_pregnant_ontime_visits():
            ppov = self.percentage_pregnant_ontime_visits()
            div_by += 1
        if self.percentage_reminded():
            pr = self.percentage_reminded()
            div_by += 1
        if self.percentage_ontime_followup():
            pof = self.percentage_ontime_followup()
            div_by += 1
        score =  pov + pobv + pom + ppov + pof + pr

        if div_by == 0:
            return None

        return int(round(score / float(div_by), 0))

    @classmethod
    def muac_summary(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        order = '-encounter__encounter_date'
        muac = NutritionReport.objects.filter(\
                                        encounter__patient__dob__gte=sixtym,
                                        encounter__patient__dob__lte=sixm)\
                                        .order_by(order)\
                                        .values('encounter__patient')\
                                        .distinct()

        num_healthy = muac.filter(\
                        status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = muac.filter(\
                        status=NutritionReport.STATUS_MODERATE).count()
        num_sam = muac.filter(\
                        status=NutritionReport.STATUS_SEVERE).count()
        num_comp = muac.filter(\
                        status=NutritionReport.STATUS_SEVERE_COMP).count()
        num_eligible = TheCHWReport.total_muac_eligible()

        unkwn = num_eligible - num_healthy - num_mam - num_sam - num_comp
        if num_eligible > 0:
            hp = int(round((num_healthy / float(num_eligible)) * 100))
            modp = int(round((num_mam / float(num_eligible)) * 100))
            svp = int(round((num_sam / float(num_eligible)) * 100))
            svcomp = int(round((num_comp / float(num_eligible)) * 100))
            unkp = int(round((unkwn / float(num_eligible)) * 100))
        else:
            hp = modp = svp = svcomp = unkp = 0

        info = _(u"[%(hel)d, %(mmod)d, %(sev)d, %(sevcomp)d, %(unkwn)d], {" \
                        "legend: [\"%(hp)d%% Healthy\", \"%(mp)d%% " \
                        "Moderate\",\"%(svp)d%% Severe\", " \
                        "\"%(scm)d%% Severe Completely\", " \
                        "\"%(unkp)d%% Unknown\"]") % \
                        {'hel': num_healthy, 'mmod': num_mam, 'sev': num_sam, \
                            'sevcomp': num_comp, 'unkwn': unkwn, 'hp': hp, \
                            'mp': modp, 'svp': svp, 'scm': svcomp, \
                            'unkp': unkp}
        return info


    @classmethod
    def muac_summary_data():
        """
        Copy/Pasted from muac_summary to get the same data but in a dict, rather than
        a string.
        """
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        order = '-encounter__encounter_date'
        muac = NutritionReport.objects.filter(\
                                        encounter__patient__dob__gte=sixtym,
                                        encounter__patient__dob__lte=sixm)\
                                        .order_by(order)\
                                        .values('encounter__patient')\
                                        .distinct()

        num_healthy = muac.filter(\
                        status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = muac.filter(\
                        status=NutritionReport.STATUS_MODERATE).count()
        num_sam = muac.filter(\
                        status=NutritionReport.STATUS_SEVERE).count()
        num_comp = muac.filter(\
                        status=NutritionReport.STATUS_SEVERE_COMP).count()
        num_eligible = TheCHWReport.total_muac_eligible()

        unkwn = num_eligible - num_healthy - num_mam - num_sam - num_comp
        if num_eligible > 0:
            hp = int(round((num_healthy / float(num_eligible)) * 100))
            modp = int(round((num_mam / float(num_eligible)) * 100))
            svp = int(round((num_sam / float(num_eligible)) * 100))
            svcomp = int(round((num_comp / float(num_eligible)) * 100))
            unkp = int(round((unkwn / float(num_eligible)) * 100))
        else:
            hp = modp = svp = svcomp = unkp = 0
        return {'healthy':hp, 'moderate': modp, 'unknown': unkp }


    @classmethod
    def total_at_risk(cls):
        num = NutritionReport.objects.filter(\
                                status__in=(NutritionReport.STATUS_SEVERE, \
                                NutritionReport.STATUS_SEVERE_COMP, \
                                NutritionReport.STATUS_MODERATE)).count()
        return num

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('alias').verbose_name.upper(), \
             'bit': '@{{ object.alias }}'})
        columns.append(
            {'name': _("Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': "No. of Patients".upper(), \
             'bit': '{{ object.num_of_patients }}'})
        columns.append(
            {'name': "No. Under 5".upper(), \
             'bit': '{{ object.num_of_underfive }}'})
        columns.append(
            {'name': "No. of Visits".upper(), \
             'bit': '{{ object.num_of_visits }}'})
        columns.append(
            {'name': "No. SAM".upper(), \
             'bit': '{{ object.num_of_sam }}'})
        columns.append(
            {'name': "No. MAM".upper(), \
             'bit': '{{ object.num_of_mam }}'})
        columns.append(
            {'name': "No. HEALTHY".upper(), \
             'bit': '{{ object.num_of_healthy }}'})
        columns.append(
            {'name': "No. SMS Sent".upper(), \
             'bit': '{{ object.num_of_sms }}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def chw_bednet_summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('location').verbose_name.upper(), \
             'bit': '{{object.location }}'})
        columns.append(
            {'name': _("Name".upper()), \
             'bit': '{{object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': "No. of House holds".upper(), \
             'bit': '{{object.number_of_households}}'})
        columns.append(
            {'name': "Household Survey Done".upper(), \
             'bit': '{{object.bednet_survey.total}}'})
        columns.append(
            {'name': "Percentage".upper(), \
             'bit': '{{object.per_bednetsurvey}}'})
        columns.append(
            {'name': "Total Sleeping site".upper(), \
             'bit': '{{object.bednet_survey.num_site}}'})
        columns.append(
            {'name': "Functioning Bednet".upper(), \
             'bit': '{{ object.bednet_survey.function}}'})
        columns.append(
            {'name': "Damaged Bednet".upper(), \
             'bit': '{{object.bednet_survey.damaged}}'})
        columns.append(
            {'name': "Earlier(b4 2009)".upper(), \
             'bit': '{{object.bednet_survey.earlier}}'})
        columns.append(
            {'name': "Required Bednet".upper(), \
             'bit': '{{object.required_bednet}}'})
        columns.append(
            {'name': "Bednet Utilization".upper(), \
             'bit': '{{object.num_netutilization}}'})
        columns.append(
            {'name': "#Sanitation ".upper(), \
             'bit': '{{object.num_sanitation}}'})
        columns.append(
            {'name': "#Drinking water ".upper(), \
             'bit': '{{object.num_drinkingwater}}'})

        sub_columns = None
        return columns, sub_columns

    @classmethod
    def sms_per_day(cls):
        days_of_the_week = seven_days_to_date()
        data = []
        for day in days_of_the_week:
            start = day_start(day['date'])
            end = day_end(day['date'])
            num = IncomingMessage.objects.filter(received__gte=start, \
                                           received__lte=end).count()
            total_error_sms = OutgoingMessage.objects.filter(sent__gte=start, \
                                           sent__lte=end, \
                                    text__icontains='error').count()
            csms = num - total_error_sms

            hvr = HouseholdVisitReport.objects.filter(\
                            encounter__encounter_date__gt=start, \
                            encounter__encounter_date__lte=end).count()
            fr = FeverReport.objects.filter(\
                            encounter__encounter_date__gt=start, \
                            encounter__encounter_date__lte=end).count()
            nutr = NutritionReport.objects.filter(\
                            encounter__encounter_date__gt=start, \
                            encounter__encounter_date__lte=end).count()

            data.append({'day': day["day"], 'total': num, \
                         'correcct_sm': csms, 'wrong_sms': total_error_sms, \
                         'muac': nutr, 'rdt': fr, 'householdv': hvr})
        return data

class OperationalReport():
    columns = []

    def __init__(self):
        percentage_template = lambda field_name: \
            ''.join(['{% ifequal object.', 
                    field_name,
                    ' None %}-{%else%}'\
                    '{{ object.',
                    field_name,
                    ' }}%{% endifequal %}'])

        columns = []
        columns.append({ \
            'name': _("CHW"),
            'abbr': _("CHW"),
            'bit': '{{object}}',
            'col': 'name'})
        columns.append({ \
            'name': _("# of Households"), \
            'abbr': _("#HH"), \
            'bit': '{{object.number_of_households}}',
            'col': 'A1'})
        columns.append({ \
            'name': _("# of Household Visits (in last 90 days)"), \
            'abbr': _("#HH-V"), \
            'bit': '{{object.num_of_householdvisits_90_days}}',
            'col': 'A2'})
        columns.append({
            'name': _("% of HHs receiving on-time routine visit "\
                                    "(within 90 days) [S23]"), \
            'abbr': _("%OTV"), \
            'bit': percentage_template('percentage_ontime_visits'),
            'col': 'A3'})
        columns.append({ \
            'name': _("# of Birth Reports"), \
            'abbr': _('#Bir'), \
            'bit': '{{object.num_of_births}}',
            'col': 'B1'})
        columns.append({ \
            'name': _("% Births delivered in "\
                                "Health Facility [S4]"),
            'abbr': _('%BHF'), \
            'bit': percentage_template('percentage_clinic_deliveries'),
            'col': 'B2'})
        columns.append({ \
            'name': _("% Newborns checked within 7 days of birth "\
                            "[S6]"), \
            'abbr': _('%NNV'), \
            'bit': percentage_template('percentage_ontime_birth_visits'),
            'col': 'B3'})
        columns.append({ \
            'name': _("# of Under-5s"), \
            'abbr': _('#U5'), \
            'bit': '{{object.num_of_underfive}}',
            'col': 'C1'})
        columns.append({
            'name': _("# Under-5 Referred for Danger Signs"), \
            'abbr': _('#U5-DS'), \
            'bit': '{{object.num_underfive_refferred}}',
            'col': 'C2'})
        columns.append({ \
            'name': _("# Under-5 Treated for Malarias"), \
            'abbr': _('#U5-Mal'), \
            'bit': '{{object.num_underfive_malaria}}',
            'col': 'C3'})
        columns.append({ \
            'name': _("# Under-5 Treated for Diarrhea"), \
            'abbr': _('#U5-Dia'), \
            'bit': '{{object.num_underfive_diarrhea}}',
            'col': 'C4'})
        columns.append({ \
            'name': _("% Under-5 receiving on-time MUAC "\
                                    "(within 90 days) [S11]"), \
            'abbr': _('#U5-MUAC'), \
            'bit': percentage_template('percentage_ontime_muac'),
            'col': 'C5'})
        columns.append({ \
            'name': _("# of Active GAM cases"), \
            'abbr': _('#U5-GAM'), \
            'bit': '{{object.num_of_active_gam_cases}}',\
            'col': 'C6' })
        columns.append({ \
            'name': _("# of Pregnant Women"), \
            'abbr': _('#PW'), \
            'bit': '{{object.num_of_pregnant_women}}',
            'col': 'D1'})
        columns.append({ \
            'name': _("# Pregnant Women Referred Urgently"),
            'abbr': _('#PW-DS'), \
            'bit': '{{object.num_pregnant_refferred}}',
            'col': 'D2'})
        columns.append({ \
            'name': _("% Pregnant receiving on-time visit"\
                        " (within 6 weeks) [S24]"), \
            'abbr': _('%PW-OTV'), \
            'bit': percentage_template('percentage_pregnant_ontime_visits'),
            'col': 'D3'})
        columns.append({ \
            'name': _("# Number of appointments"), \
            'abbr': _('%NOA'), \
            'bit': '{{ object.num_of_appointment }}',
            'col': 'E1'})
        columns.append({ \
            'name': _("% of appointment reminders completed"), \
            'abbr': _('%POA-RT'), \
            'bit': percentage_template('percentage_reminded'),
            'col': 'E2'})
        columns.append({ \
            'name': _("% Urgently referred receiving on-time "\
                            "follow-up (within 2 days) [S13]"),
            'abbr': _('%Ref'), \
            'bit': percentage_template('percentage_ontime_followup'),
            'col': 'F1'})
        columns.append({ \
            'name': _("Median # of days for follow-up [S25]"), \
            'abbr': _('#Fol'), \
            'bit': '{{object.median_number_of_followup_days}}',
            'col': 'F2'})
        columns.append({ \
            'name': _("SMS Error Rate %"), \
            'abbr': _('%Err'), \
            'bit': percentage_template('sms_error_rate'),
            'col': 'G1'})
        columns.append({ \
            'name': _("Days since last SMS transmission"), \
            'abbr': _('#Days'), \
            'bit': '{{ object.days_since_last_sms|default_if_none:"-" }}',
            'col': 'G2'})
        columns.append({ \
            'name': _("Calculated overall CHW performance indicator"), \
            'abbr': _('SCORE'), \
            'bit': percentage_template('score'),
            'col': 'H1'})
        self.columns = columns

    def get_columns(self):
        return self.columns


class GraphicalClinicReport(Clinic):
    class Meta:
        verbose_name = _("Graphical Clinic Report")
        proxy = True

    # This is not good. We need to be able to get the
    # number of indicators from the class, but can't
    # look at .indicators() directly unless the object
    # is instantiated
    @classmethod
    def n_indicators(self):
        return 4

    def indicators(self):
        return [\
            Indicator(_(u'Percentage of Children 6m-59m Old '\
                        'Getting at Least 1 MUAC in the Last '\
                        '3 Months (or 1 month for SAM/MAM cases)'),\
                        self.percentage_ontime_muac,\
                        Indicator.AGG_PERCS, Indicator.PERC_PRINT),\
            Indicator(_(u'Percentage of Under-Fives with Known '\
                        'Up-to-date Immunizations'),\
                        self.percentage_known_immunized,
                        Indicator.AGG_PERCS, Indicator.PERC_PRINT),\
            Indicator(_(u'Percentage of Pregnant Women Having '\
                        'at Least 4 ANC Visits by Birth'),\
                        self.percentage_with_four_anc,
                        Indicator.AGG_PERCS, Indicator.PERC_PRINT),\
            Indicator(_(u'Percentage On-Time Follow-Up '\
                        '(within 3 days of a Basic, Emergency, or '\
                        'Ambulance referral)'),\
                        self.percentage_ontime_follow_up,
                        Indicator.AGG_PERCS, Indicator.PERC_PRINT),\
        ]

    def _aggregate_clinic_percentage(self, agg_func):
        chws = MonthlyCHWReport\
            .objects\
            .filter(clinic=self, is_active=True)

        if chws.count() == 0:
            return None

        num = 0
        den = 0
        for c in chws:
            out = agg_func(c)
            print out
            if out is None: continue

            (n,d) = out
            num += n
            den += d

        print (num, den)
        if den == 0:
            return None
        return (num, den)
 

    def percentage_with_four_anc(self, per_cls, per_num):
        return self._aggregate_clinic_percentage(\
            lambda c: c.perc_with_anc_four(per_cls, per_num))
           
    def percentage_ontime_follow_up(self, per_cls, per_num):
        return self._aggregate_clinic_percentage(\
            lambda c: \
                c.percentage_ontime_followup(\
                    per_cls.period_start_date(per_num),\
                    per_cls.period_end_date(per_num), \
                    True))

    def _underfive_at_per(self, per_cls, per_num):
        end_date = per_cls.period_end_date(per_num)

        # Get active patients for this CHW who were aged 6-59m
        # during the time period we're talking about
        return ThePatient.objects.filter(\
            chw__clinic=self, \
            chw__is_active=True, \
            status=Patient.STATUS_ACTIVE, \
            dob__lte = end_date - timedelta(30.475 * 6),
            dob__gte = end_date - timedelta(30.475 * 59))

    def percentage_known_immunized(self, per_cls, per_num):
        end_date = per_cls.period_end_date(per_num)
        try:
            patients = self._underfive_at_per(per_cls, per_num)
        except ThePatient.DoesNotExist:
            return None

        if patients.count() == 0:
            return None

        count = 0
        for p in patients:
            if p.is_immunized():
                count += 1

        return (count, patients.count())

    def percentage_ontime_muac(self, per_cls, per_num):
        end_date = per_cls.period_end_date(per_num)
        try:
            patients = self._underfive_at_per(per_cls, per_num)
        except ThePatient.DoesNotExist:
            return None

        if patients.count() == 0:
            return None

        ontimes = 0
        for patient in patients:
            if patient.ontime_muac(end_date):
                ontimes += 1

        return (ontimes, patients.count())

class ClinicReport(Clinic):
    class Meta:
        verbose_name = _("Clinic Report")
        proxy = True

    @property
    def registeredpatient(self):
        total = Patient.objects.filter(chw__location=self)
        return total.count()

    @property
    def househoulds(self):
        thousehold = Patient.objects.filter(health_id=F(\
                                                    'household__health_id'),\
                                        chw__location=self)
        return thousehold.count()

    @property
    def pntied_household(self):
        nttied_household = Patient.objects.filter(chw__location=self,\
                                            household__health_id='xxxxx')
        return nttied_household.count()

    @property
    def rdtreported(self):
        fr = FeverReport.objects.filter(encounter__patient__chw__location=self)
        return fr.count()

    @property
    def hvisit(self):
        hvisit = HouseholdVisitReport.objects.filter(\
                                    encounter__patient__chw__location=self)
        return hvisit.count()

    @property
    def muacreport(self):
        muac = NutritionReport.objects.filter(\
                                    encounter__patient__chw__location=self)
        return muac.count()

    def monthly_summary(self, month=None, year=None):
        if not month:
            month = datetime.today().month
        if not year:
            year = datetime.today().year
        onfirst = datetime(year=year, month=month, day=1)
        rdt = FeverReport.objects.filter(encounter__patient__clinic=self, \
                                    encounter__encounter_date__month=month, \
                                    encounter__encounter_date__year=year)\
                                .count()
        prdt = FeverReport.objects.filter(encounter__patient__clinic=self, \
                                    encounter__encounter_date__month=month, \
                                    encounter__encounter_date__year=year, \
                                    rdt_result=FeverReport.RDT_POSITIVE)\
                                .count()

        nut = NutritionReport.objects.filter(encounter__patient__clinic=self, \
                                    encounter__encounter_date__month=month, \
                                    encounter__encounter_date__year=year)\
                                .count()
        snut = NutritionReport.objects.filter(encounter__patient__clinic=self,\
                                encounter__encounter_date__month=month, \
                                encounter__encounter_date__year=year, \
                                status__in=(NutritionReport.STATUS_SEVERE, \
                                NutritionReport.STATUS_SEVERE_COMP, \
                                NutritionReport.STATUS_MODERATE))\
                                .count()
        return {'clinic': self,
                'month': onfirst.strftime("%B"),
                'rdt': rdt,
                'positive_rdt': prdt,
                'nutrition': nut,
                'malnutrition': snut}

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': cls._meta.get_field('name').verbose_name.upper(), \
             'bit': '{{object.name}}'})
        columns.append(
            {'name': _("# of Household".upper()), \
             'bit': '{{object.househoulds}}'})
        columns.append(
            {'name': _("#House visits".upper()), \
             'bit': '{{object.hvisit}}'})
        columns.append(
            {'name': _("#Patients".upper()), \
             'bit': '{{object.registeredpatient}}'})
        columns.append(
            {'name': _("#MUAC".upper()), \
             'bit': '{{object.muacreport}}'})
        columns.append(
            {'name': "#RDT ".upper(), \
             'bit': '{{object.rdtreported}}'})

        sub_columns = None
        return columns, sub_columns


class SummaryReport():

    '''Cluster-wide Summary Reports'''

    def num_of_patients(self):
        return Patient.objects.all().count()

    def num_of_underfive(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym).count()

    def num_of_households(self):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_pregnant(self):
        c = 0
        pregs = PregnancyReport.objects.filter()\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        return {"summary": {"num_underfive": sr.num_of_underfive(), \
                            "num_patients": sr.num_of_patients(), \
                            "num_households": sr.num_of_households(), \
                            "num_pregnant": sr.num_pregnant()}}


class WeekSummaryReport():

    '''This week Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter(created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym, \
                                      created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def savgummary(cls):
        sr = cls()
        endDate = datetime.today()
        startDate = endDate - timedelta(endDate.weekday())

        return {"week_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class MonthSummaryReport():

    '''This month Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter(created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym, \
                                      created_on__gte=startDate, \
                                      created_on__lte=endDate).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_MODERATE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()

        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter(\
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        endDate = last_day_of_month(datetime.today())
        startDate = first_day_of_month(datetime.today())

        return {"month_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class GeneralSummaryReport():

    '''This month Summary Reports'''
    def num_of_patients(self, startDate=None, endDate=None):
        return Patient.objects.filter().count()

    def num_of_underfive(self, startDate=None, endDate=None):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(dob__gte=sixtym).count()

    def num_of_households(self, startDate=None, endDate=None):
        return Patient.objects\
                    .filter(health_id=F('household__health_id')).count()

    def num_of_muac(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(\
                            status=NutritionReport.STATUS_MODERATE).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE_COMP).count()


        return num

    def num_of_rdts(self, startDate=None, endDate=None):
        return FeverReport.objects.filter().count()

    def num_pregnant(self, startDate=None, endDate=None):
        c = 0
        pregs = PregnancyReport.objects.filter()\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c += 1
        return c

    @classmethod
    def summary(cls):
        sr = cls()
        endDate = last_day_of_month(datetime.today())
        startDate = first_day_of_month(datetime.today())

        return {"general_summary_report": {"num_mam_sam": sr.num_of_muac(\
                                    startDate=startDate, endDate=endDate), \
                            "num_rdt": sr.num_of_rdts( \
                                    startDate=startDate, endDate=endDate), \
                            "num_pregnant": sr.num_pregnant( \
                                    startDate=startDate, endDate=endDate)}}


class TheBHSurveyReport(TheCHWReport):
    '''
    The Bednet Household Healthy Survey Report
    '''
    class Meta:
        verbose_name = _(u"The Bednet Household Healthy Survey Report")
        proxy = True

    def bednet_aggregates(self):
        data = BedNetReport.objects.filter(encounter__chw=self)\
                                    .aggregate(Avg('sleeping_sites'),
                                    Count('encounter'),
                                    Sum('sleeping_sites'),
                                    Sum('function_nets'),
                                    Sum('earlier_nets'),
                                    Sum('damaged_nets'))
        bednet_util = BednetUtilization.objects.filter(encounter__chw=self)\
                                                .aggregate(Count('encounter'))
        data.update({'bednet_util__count': bednet_util['encounter__count']})
        dwr = DrinkingWaterReport.objects.filter(encounter__chw=self)\
                                                .aggregate(Count('encounter'))
        data.update({'drinking_water__count': dwr['encounter__count']})
        sanitation = SanitationReport.objects.filter(encounter__chw=self)\
                                                .aggregate(Count('encounter'))
        data.update({'sanitation__count': sanitation['encounter__count']})
        for item in data:
            if data[item] is None:
                data[item] = '-'
        return data

    @classmethod
    def healthy_survey_columns(cls):
        columns = []
        columns.append({'name': _(u"CHW"), 'bit': '{{object}} '\
                                            '{{object.mobile_phone}}'})
        columns.append({'name': _(u"# of Households"), \
                'bit': '{{object.number_of_households}}'})
        columns.append({'name': _(u"# of HH Visits (Last two weeks)"), \
                'bit': '{{object.two_weeks_visits}}'})
        columns.append({'name': _(u"# of Households Surveyed"), \
                'bit': '{{object.bednet_aggregates.encounter__count}}'})
        columns.append({'name': _(u"# of Sleeping Sites"), \
                'bit': '{{object.bednet_aggregates.sleeping_sites__sum}}'})
        columns.append({'name': _(u"# of Functioning Bednets"), \
                'bit': '{{object.bednet_aggregates.function_nets__sum}}'})
        columns.append({'name': _(u"# of damaged"), \
                'bit': '{{object.bednet_aggregates.damaged_nets__sum}}'})
        columns.append({'name': _(u"# of Earlier Bednets"), \
                'bit': '{{object.bednet_aggregates.earlier_nets__sum}}'})
        columns.append({'name': _(u"# of Bednet Utilization Reports"), \
                'bit': '{{object.bednet_aggregates.bednet_util__count}}'})
        columns.append({'name': _(u"# of Drinking Water Reports"), \
                'bit': '{{object.bednet_aggregates.drinking_water__count}}'})
        columns.append({'name': _(u"# of Sanitation Reports"), \
                'bit': '{{object.bednet_aggregates.sanitation__count}}'})

        return columns

    def households_not_surveyed(self):
        surveyed = BedNetReport.objects.filter(encounter__chw=self)\
                                        .values('encounter__patient')
        not_surveyed = self.households().exclude(id__in=surveyed)
        return not_surveyed

'''
    The monthly report for CHWs requested
    by Dr. Emma.  The code is not great
    but I don't have any good ideas for
    how to shrink the size.
'''

class MonthlyCHWReport(TheCHWReport):
    class Meta:
        proxy = True

    def report_groups(self):
        return [
            {'title': _(u'Household'), 'length': 3},
            {'title': _(u'Family Planning'), 'length': 3},
            {'title': _(u'Follow Up'), 'length': 5},
            {'title': _(u'Pregnancy'), 'length': 5},
            {'title': _(u'Under Five'), 'length': 4},
            {'title': _(u'Malaria'), 'length': 3},
            {'title': _(u'Diarrhea'), 'length': 2},
        ]

    # The report rows.  Returns a list of tuples
    # that can be used to instantiate Indicator objects
    def report_indicators(self):
        return [
            Indicator('Households',\
                self.num_of_hhs, Indicator.AVG, \
                col_agg_func = Indicator.SUM),
            Indicator('Total HH Visits',\
                self.total_hh_visits, Indicator.SUM),
            #Indicator('Unique HH Visits',\
            #    self.num_of_hh_visits, Indicator.SUM),
            Indicator('Percentage of HHs Getting Visit in Last 90 Days',\
                self.perc_ontime_hh_visits,
                Indicator.AGG_PERCS, Indicator.PERC_PRINT_SHORT),
            INDICATOR_EMPTY,
            Indicator('Num of Women 15-49 Seen',\
                self.num_of_women_under50_seen, Indicator.SUM),
            Indicator('Women using FP',\
                self.num_of_women_under50_using_fp, Indicator.SUM),
            #Indicator('% of Women using FP',\
            #    self.perc_of_women_under50_using_fp, \
            #        Indicator.AGG_PERCS, \
            #        Indicator.PERC_PRINT),
            #Indicator('Num of Women using FP: Condom',\
            #    self.num_fp_usage_condom, Indicator.SUM),
            #Indicator('Num of Women using FP: Injectable',\
            #    self.num_fp_usage_injectable, Indicator.SUM),
            #Indicator('Num of Women using FP: IUD',\
            #    self.num_fp_usage_iud, Indicator.SUM),
            #Indicator('Num of Women using FP: Implant',\
            #    self.num_fp_usage_implant, Indicator.SUM),
            #Indicator('Num of Women using FP: Pill',\
            #    self.num_fp_usage_pill, Indicator.SUM),
            #Indicator('Num of Women using FP: Ster.',\
            #    self.num_fp_usage_sterilization, Indicator.SUM),
            Indicator('Women Starting FP or Never Registered',\
                self.num_starting_fp, Indicator.SUM),
            #Indicator('Num of Women Remaining on FP',\
            #    self.num_still_on_fp, Indicator.SUM),
            #Indicator('Num of Women Stopping FP',\
            #    self.num_ending_fp, Indicator.SUM),
            INDICATOR_EMPTY,
            Indicator('People with DSs',\
                self.num_danger_signs, Indicator.SUM),
            Indicator('Urgent (non-convenient) Referrals',\
                self.num_referred, Indicator.SUM),
            Indicator('On-Time Follow Up Visits (within 3 days)',\
                self.num_ontime_follow_up, Indicator.SUM),
            Indicator('Late Follow Up Visits (within 7 days)',\
                self.num_late_follow_up, Indicator.SUM),
            Indicator('No Follow Up Visits (never or after 7 days)',\
                self.num_never_follow_up, Indicator.SUM),
            #Indicator('% Follow Up Within 3 Days',\
            #    self.perc_ontime_follow_up,
            #    Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            INDICATOR_EMPTY,
            Indicator('Pregnant Women',\
                self.num_pregnant_by_period, Indicator.AVG,\
                col_agg_func=Indicator.SUM),
            #Indicator('% Getting 1 ANC by 1st Trim.',\
            #    self.perc_with_anc_first,
            #    Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            #Indicator('% Getting 3 ANC by 2nd Trim.',\
            #    self.perc_with_anc_second,
            #    Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('Births',\
                self.num_births, Indicator.SUM),
            Indicator('Births with 4 ANC',\
                self.num_births_with_anc_four, Indicator.SUM),
            Indicator('Babies Known Delivered in Clinic',\
                self.num_births_delivered_in_facility, Indicator.SUM),
            #Indicator('% Getting 4 ANC by Birth',\
            #    self.perc_with_anc_four,
            #    Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('Neonatal Reports (within 7 days)',\
                self.num_neonatal, Indicator.SUM),
            INDICATOR_EMPTY,
            Indicator('Children U5',\
                self.num_underfive, Indicator.AVG,\
                col_agg_func=Indicator.SUM),
            Indicator('Children U5 Known Immunized',\
                self.num_underfive_imm, Indicator.AVG,\
                col_agg_func=Indicator.SUM),
            Indicator('MUACs Taken',\
                self.num_muacs_taken, Indicator.SUM),
            Indicator('Active SAM/MAM Cases',\
                self.num_active_sam_cases, Indicator.AVG,\
                col_agg_func=Indicator.SUM),
            Indicator('Tested RDTs',\
                self.num_tested_rdts, Indicator.SUM),
            Indicator('Positive RDTs',\
                self.num_positive_rdts, Indicator.SUM),
            Indicator('Anti-Malarials Given',\
                self.num_antimalarials_given, Indicator.SUM),
            Indicator('Diarrhea Cases',\
                self.num_diarrhea, Indicator.SUM),
            Indicator('ORS Given',\
                self.num_ors_given, Indicator.SUM),
        ]

    #
    # HH Visit section
    #

    def num_of_hhs(self, per_cls, per_num):
        return self.households(\
            per_cls.period_end_date(per_num)).count()

    def num_diarrhea(self, per_cls, per_num):
        return DangerSignsReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(danger_signs__code='dr')\
            .count()

    def num_ors_given(self, per_cls, per_num):
        return MedicineGivenReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(medicines__code='r')\
            .count()

    def total_hh_visits(self, per_cls, per_num):
        return HouseholdVisitReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .count()

    # We're going for distinct households, not
    # just raw household visits
    def num_of_hh_visits(self, per_cls, per_num):
        return HouseholdVisitReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .values('encounter__patient__household__pk')\
            .distinct()\
            .count()

    def num_of_hhs(self, per_cls, per_num):
        return self.households(\
            per_cls.period_end_date(per_num)).count()

    def num_of_hh_visits_in_90days(self, per_cls, per_num):
        end_date = per_cls.period_end_date(per_num)
        start_date = end_date - timedelta(90)
        return HouseholdVisitReport\
            .indicators\
            .filter(encounter__patient__chw=self,\
                encounter__encounter_date__gte=start_date, \
                encounter__encounter_date__lte=end_date)\
            .values('encounter__patient')\
            .distinct()\
            .count()

    def perc_ontime_hh_visits(self, per_cls, per_num):
        return (self.num_of_hh_visits_in_90days(per_cls, per_num), \
            self.num_of_hhs(per_cls, per_num))

    #
    # Family planning section
    #

    def num_of_women_under50_seen(self, per_cls, per_num):
        return self._num_of_women_count(per_cls, per_num, 'women')

    def num_of_women_under50_using_fp(self, per_cls, per_num):
        return self._num_of_women_count(per_cls, per_num, 'women_using')

    def perc_of_women_under50_using_fp(self, per_cls, per_num):
        u50 = self.num_of_women_under50_seen(per_cls, per_num)
        return (self.num_of_women_under50_using_fp(per_cls, per_num), u50)

    def _num_of_women_count(self, per_cls, per_num, count_str):
        if count_str not in ['women','women_using']:
            raise ValueError('Invalid aggregation string.')

        count = FamilyPlanningReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .aggregate(Sum(count_str))[count_str+'__sum']
        return 0 if count is None else count

    def num_fp_usage_condom(self, per_cls, per_num):
        return self._fp_usage_count(per_cls, per_num, 'c')

    def num_fp_usage_injectable(self, per_cls, per_num):
        return self._fp_usage_count(per_cls, per_num, 'i')

    def num_fp_usage_iud(self, per_cls, per_num):
        return self._fp_usage_count(per_cls, per_num, 'iud')

    def num_fp_usage_implant(self, per_cls, per_num):
        return self._fp_usage_count(per_cls, per_num, 'n')

    def num_fp_usage_pill(self, per_cls, per_num):
        return self._fp_usage_count(per_cls, per_num, 'p')

    def num_fp_usage_sterilization(self, per_cls, per_num):
        return self._fp_usage_count(per_cls, per_num, 'st')

    def _fp_usage_count(self, per_cls, per_num, code):
        fp = CodedItem\
            .objects\
            .filter(type=CodedItem.TYPE_FAMILY_PLANNING)\
            .get(code=code)

        count = FamilyPlanningReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(familyplanningusage__method__code=fp.code)\
            .aggregate(Sum('familyplanningusage__count'))\
            ['familyplanningusage__count__sum']
        return 0 if count is None else count

    def num_starting_fp(self, per_cls, per_num):
        return self._fp_change_stats(per_cls, per_num)[0]

    def num_still_on_fp(self, per_cls, per_num):
        return self._fp_change_stats(per_cls, per_num)[1]

    def num_ending_fp(self, per_cls, per_num):
        return self._fp_change_stats(per_cls, per_num)[2]

    def _fp_change_stats(self, per_cls, per_num):
        reps = FamilyPlanningReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .order_by('-encounter__encounter_date')

        start_count = 0
        same_count = 0
        end_count = 0

        seen = []

        # Get all FP reports in this week
        for r in reps:
            # Count each household only once
            if r.encounter.patient.pk in seen:
                continue
            else:
                seen.append(r.encounter.patient.pk)

            try:
                # Check if there's a previous FP report for this HH
                old_rep = FamilyPlanningReport\
                    .indicators\
                    .filter(encounter__patient__pk=r.encounter.patient.pk,\
                        encounter__encounter_date__lt=r.encounter.encounter_date)\
                    .exclude(pk=r.pk)\
                    .latest('encounter__encounter_date')
            except FamilyPlanningReport.DoesNotExist:
                # If not, count all women as new to FP
                if r.women_using is not None:
                    start_count += r.women_using
            else:
                if r.women_using is None:
                    if old_rep.women_using is None: continue
                    end_count += old_rep.women_using
                elif old_rep.women_using is None:
                    if r.women_using is None: continue
                    start_count += r.women_using
                else:
                    # Otherwise calculate change from last FP report
                    if r.women_using > old_rep.women_using:
                        start_count += (r.women_using - old_rep.women_using)
                    elif r.women_using < old_rep.women_using:
                        end_count += (old_rep.women_using - r.women_using)
                    else:
                        same_count += r.women_using

        return (start_count, same_count, end_count)

    #
    # Danger signs section
    #

    def num_danger_signs(self, per_cls, per_num):
        count = DangerSignsReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .count()
        return 0 if count is None else count

    def num_referred(self, per_cls, per_num):
        return ReferralReport\
                .indicators\
                .for_chw(self)\
                .for_period(per_cls, per_num)\
                .exclude(urgency=ReferralReport.URGENCY_CONVENIENT)\
                .count()

    def num_ontime_follow_up(self, per_cls, per_num):
        ontime, late, never = self._calc_ontime_follow_up(per_cls, per_num)
        return ontime

    def num_late_follow_up(self, per_cls, per_num):
        ontime, late, never = self._calc_ontime_follow_up(per_cls, per_num)
        return late

    def num_never_follow_up(self, per_cls, per_num):
        ontime, late, never = self._calc_ontime_follow_up(per_cls, per_num)
        return never

    def _calc_ontime_follow_up(self, per_cls, per_num):
        ontime = 0
        late = 0
        never = 0
        for r in ReferralReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .exclude(urgency=ReferralReport.URGENCY_CONVENIENT):

            f = FollowUpReport\
                .indicators\
                .for_chw(self)\
                .filter(encounter__patient__pk=r.encounter.patient.pk,\
                    encounter__encounter_date__gt=\
                        r.encounter.encounter_date)\
                .order_by('encounter__encounter_date')

            due_by = r.encounter.encounter_date + timedelta(3)
            late_before = r.encounter.encounter_date + timedelta(7)
            if f.count() == 0:
                never += 1
            elif f[0].encounter.encounter_date <= due_by:
                ontime += 1
            elif f[0].encounter.encounter_date > due_by and \
                    f[0].encounter.encounter_date <= late_before:
                late += 1
            else:
                # If FU visit doesn't happen with 1 week,
                # then it's not a follow-up visit at all
                never += 1
        return (ontime, late, never)

    def perc_ontime_follow_up(self, per_cls, per_num):
        return (self.num_ontime_follow_up(per_cls, per_num),\
            self.num_referred(per_cls, per_num))

    #
    # Pregnancy section
    #

    def pregnant_by_period(self, per_cls, per_num):
        return self.pregnant_women(per_cls.period_end_date(per_num))

    def num_pregnant_by_period(self, per_cls, per_num):
        return len(self.pregnant_by_period(per_cls, per_num))

    # % of women getting at least 1 ANC visit by 1st trimester
    def perc_with_anc_first(self, per_cls, per_num):
        return self._women_getting_n_anc_by(per_cls, per_num, 1, 1)

    # % of women getting at least 3 ANC visits by 2nd trimester
    def perc_with_anc_second(self, per_cls, per_num):
        return self._women_getting_n_anc_by(per_cls, per_num, 3, 2)

    def perc_with_anc_four(self, per_cls, per_num):
        return (self.num_births_with_anc_four(per_cls, per_num), \
            self.num_births(per_cls, per_num))

    def _women_getting_n_anc_by_tot(self, per_cls, \
            n_anc, trimester):

        if trimester not in xrange(1,5):
            raise ValueError('Trimester is out of range [1,4]')

        women = []
        for period in xrange(0, per_cls.num_periods):
            for w in self._women_in_month_of_preg(per_cls, per_num, trimester):
                if w not in women:
                    women.append(w)
        print women
        have_anc = filter(lambda w: w.anc_visits > n_anc, women)

        return (len(have_anc), len(women))

    def _women_getting_n_anc_by(self, per_cls, per_num, n_anc, trimester):
        if trimester not in xrange(1,5):
            raise ValueError('Trimester is out of range [1,4]')

        women = self._women_in_month_of_preg(per_cls, per_num, trimester)
        print women
        for w in women:
            print (w, w.anc_visits)
        have_anc = filter(lambda w: w.anc_visits >= n_anc, women)

        return (len(have_anc), len(women))

    def _women_in_month_of_preg(self, per_cls, per_num, trimester):
    
        if trimester not in xrange(1,5):
            raise ValueError('Trimester is out of range [1,4]')

        # e.g., 2nd trimester is range(4, 7)
        end_mo = (trimester*3)+1
        start_mo = end_mo - 3
        month_range = xrange(start_mo, end_mo)

        women = self.pregnant_by_period(per_cls, per_num)
        print women

        # Get latest pregnancy report for woman
        pregreps = []
        for w in women:
            try:
                rep = PregnancyReport\
                    .objects\
                    .filter(encounter__patient=w, \
                        encounter__encounter_date__gte=\
                            per_cls.period_end_date(per_num) - \
                                timedelta(30.4375 * 10),
                        encounter__encounter_date__lte=\
                            per_cls.period_end_date(per_num))\
                    .latest('encounter__encounter_date')
            except PregnancyReport.DoesNotExist:
                continue
            else:
                print "> found %s" % rep
                pregreps.append(rep)

        # See how many women fall in this trimester
        targets = []
        for p in pregreps:
            days_ago = (per_cls.period_end_date(per_num) - \
                p.encounter.encounter_date.date()).days
            months_ago = days_ago / 30.4375
            months_of_preg = p.pregnancy_month + months_ago

            print "women %d days from %s was in m%d => now %d" % \
                (days_ago, per_cls.period_end_date(per_num),
                    p.pregnancy_month, months_of_preg)
            if round(months_of_preg) in month_range:
                print "ok"
                targets.append(p)

        return targets

    def _births(self, per_cls, per_num):
        seen = []
        rpts = BirthReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)
        for r in rpts:
            if r.encounter.patient.pk not in seen:
                seen.append(r.encounter.patient.pk)

        patients = Patient\
            .objects\
            .filter(chw=self, \
                dob__gte=per_cls.period_start_date(per_num), \
                dob__lte=per_cls.period_end_date(per_num))
        for p in patients:
            if p.pk not in seen:
                seen.append(p.pk)

        return Patient.objects.filter(pk__in=seen)

    def num_births(self, per_cls, per_num):
        return self._births(per_cls, per_num).count()

    def num_births_with_anc_four(self, per_cls, per_num):
        babies = self._births(per_cls, per_num)
        count = 0
        sdate = per_cls.period_start_date(per_num)
        edate = per_cls.period_end_date(per_num)
        for b in babies:
            if b.mother is None:
                continue
            mother = b.mother

            try:
                prep = PregnancyReport\
                    .objects\
                    .filter(encounter__patient=mother)\
                    .filter(encounter__encounter_date__gte=sdate-timedelta(30.4375 * 10),\
                        encounter__encounter_date__lte=edate)\
                    .latest('encounter__encounter_date')
            except PregnancyReport.DoesNotExist:
                continue

            # 4 is number of ANC visits to have at term
            if prep.anc_visits >= 4:
                count += 1

        return count

    def num_births_delivered_in_facility(self, per_cls, per_num):
         return BirthReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def num_neonatal(self, per_cls, per_num):
        count = 0
        rpts = NeonatalReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)

        for r in rpts:
            if r.encounter.encounter_date.date() - timedelta(7) <= \
                r.encounter.patient.dob:
                count += 1

        return count

    def num_underfive(self, per_cls, per_num):
        return self.patients_under_five(\
            per_cls.period_end_date(per_num)).count()

    def num_underfive_imm(self, per_cls, per_num):
        return len(self._num_underfive_imm_pks(per_cls, per_num))

    def _num_underfive_imm_pks(self, per_cls=None, per_num=None):
        if per_cls is None:
            end_date = date.today()
        else:
            end_date = per_cls.period_end_date(per_num)

        immd = []

        # Get all kids under five
        kids = self.patients_under_five(end_date)

        print "kids: %d" % kids.count()
        for k in kids:
            try:
                imm = UnderOneReport\
                    .indicators\
                    .filter(encounter__patient=k)\
                    .latest()
            except UnderOneReport.DoesNotExist:
                print 'no im'
                continue

            if imm.immunized != UnderOneReport.IMMUNIZED_YES:
                continue

            if k.dob + timedelta(365) <= end_date:
                # logic for one-year-olds

                # Make sure they've been checked to be up-to-date on
                # immunizations in the last 3 months
                print 'u1'
                if imm.encounter.encounter_date.date() >= \
                            end_date - timedelta(3 * 30.3475):
                    immd.append(k.pk)
                else:
                    print 'too late: %s %s' % (k.dob, imm.encounter.encounter_date)
                    
            else:
                # All kids over one year old with up-to-date
                # immunizations are up-to-date
                print 'u5'
                immd.append(k.pk)

        print immd
        print len(immd)
        return immd

    def num_muacs_taken(self, per_cls, per_num):
        return NutritionReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(muac__isnull=False, status__isnull=False)\
            .count()

    def num_active_sam_cases(self, per_cls, per_num):
        return self.num_of_active_sam_cases(\
            per_cls.period_end_date(per_num))

    def num_tested_rdts(self, per_cls, per_num):
        return FeverReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .exclude(rdt_result=FeverReport.RDT_UNKOWN)\
            .count()

    def num_positive_rdts(self, per_cls, per_num):
        return FeverReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(rdt_result=FeverReport.RDT_POSITIVE)\
            .count()

    def num_antimalarials_given(self, per_cls, per_num):
        return MedicineGivenReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(medicines__code='act')\
            .count()

    def num_diarrhea(self, per_cls, per_num):
        return DangerSignsReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(danger_signs__code='dr')\
            .count()

    def num_ors_given(self, per_cls, per_num):
        return MedicineGivenReport\
            .indicators\
            .for_chw(self)\
            .for_period(per_cls, per_num)\
            .filter(medicines__code='r')\
            .count()

    #
    # Lists
    #

    # People lacking follow-up in last 45 days
    def lacking_follow_up(self):
        out = self.people_without_followup(date.today() - timedelta(45))
        if out is None:
            return []
        (fup, nofup) = out

        entries = []
        for ref in nofup:
            entries.append(self._dict_for_follow_up(ref))

        return entries

    def _dict_for_follow_up(self, ref):
        e = ref.encounter
        all_ds = DangerSignsReport.objects.filter(encounter=e)
        ds = all_ds[0] if (all_ds.count() > 0) else None

        all_fu = FollowUpReport\
            .objects\
            .filter(encounter__patient=e.patient, \
                encounter__encounter_date__gt=\
                    ref.encounter.encounter_date)\
            .order_by('encounter__encounter_date')
        fu = all_fu[0] if (all_fu.count() > 0) else None

        return {
            'referral': ref,
            'danger_signs': ds,
            'follow_up': fu,
            }
        
    # Kids under 5 yrs needing immunizations
    def needing_immunizations(self):
        imm_pks = self._num_underfive_imm_pks(MonthlyPeriodSet, 3)

        return ThePatient\
            .objects\
            .exclude(pk__in=imm_pks)\
            .filter(chw=self,\
                status=Patient.STATUS_ACTIVE,\
                dob__gte = date.today()-timedelta(5*365.25))\
            .order_by('location__code')

    # Pregnant women in 2nd or 3rd trimester who haven't had
    # ANC visits in last 5 five weeks
    def pregnant_needing_anc(self):
        pregs = PregnancyReport\
            .indicators\
            .for_chw(self)\
            .filter(encounter__encounter_date__gt = \
                date.today() - timedelta(10 * 30.4375))\
            .order_by('-encounter__encounter_date')

        seen = []
        no_anc = []
        women = []
        for p in pregs:
            if p.encounter.patient.pk in seen:
                continue
            else:
                seen.append(p.encounter.patient.pk)

            days_ago = (datetime.today() - p.encounter.encounter_date).days
            weeks_ago = days_ago / 7.0
            months_ago = days_ago / 30.4375

            # Current month of pregnancy
            preg_month = p.pregnancy_month + months_ago
            if preg_month > 9.0 or preg_month < 3.0:
                continue

            print "%s %d %d" % (p.encounter.encounter_date, p.pregnancy_month, preg_month)
            months_left = 9 - preg_month
            days_left = months_left * 30.475
            due_date = date.today() + timedelta(days_left)

            # Current weeks since ANC
            if p.weeks_since_anc is None:
                no_anc.append((p.encounter.patient, \
                    None,\
                    due_date))
            else:
                weeks_since_anc = p.weeks_since_anc + weeks_ago
                if weeks_since_anc > 5.0:
                    women.append((p.encounter.patient, \
                        p.encounter.encounter_date - \
                            timedelta(7 * p.weeks_since_anc), \
                        due_date))

        women.sort(lambda x,y: cmp(x[1],y[1]))
        return (no_anc + women)

    def kids_needing_muac(self):
        # people eligible for MUAC
        muac_list = self.muac_list()\
            .order_by('encounter__patient__location__code')

        seen = []
        need_muac = []
        no_muac = []

        one_month_ago = datetime.today() - timedelta(30.4375)
        three_months_ago = datetime.today() - timedelta(3 * 30.4375)

        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        for p in muac_list:
            if p.pk in seen:
                continue
            else:
                seen.append(p.pk)

            try:
                nut = NutritionReport\
                    .objects\
                    .filter(encounter__patient__pk=p.pk,
                        muac__isnull=False,
                        status__isnull=False)\
                    .latest('encounter__encounter_date')
            except NutritionReport.DoesNotExist:
                no_muac.append((p, None))
                continue

            if nut.status in danger and \
                    nut.encounter.encounter_date < one_month_ago:
                need_muac.append((p, nut))
            elif nut.encounter.encounter_date < three_months_ago:
                need_muac.append((p, nut))
            else:
                pass

        need_muac.sort(lambda x,y:\
            cmp(x[1].encounter.encounter_date, \
                y[1].encounter.encounter_date))
        return no_muac + need_muac


class HealthCoordinatorReport():
    # The report rows.  Returns a list of tuples
    # that can be used to instantiate Indicator objects
    def report_indicators(self):
        return [
            Indicator('Health Outcome Indicators',\
                Indicator.empty_func, Indicator.empty_func),
            Indicator('% of Women using FP',\
                self.perc_of_women_under50_using_fp, \
                    Indicator.AGG_PERCS, \
                    Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_of_women_under50_seen, Indicator.SUM),
            Indicator('% Getting 1 ANC by 2nd Trim.',\
                self.perc_with_anc_second, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_women_in_second, Indicator.SUM),
            Indicator('% Getting 4 ANC by Birth',\
                self.perc_with_anc_four, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_women_in_third, Indicator.SUM),
            Indicator('% Births Delivered in Health Facility',\
                self.perc_births_delivered_in_facility, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_births, Indicator.SUM),
            Indicator('% Births with Low birth Weight',\
                self.perc_births_with_low_weight, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_births_delivered_in_facility, Indicator.SUM),
            Indicator('% Under 1 Exclusively Breast Fed',\
                self.perc_underone_exclusively_bf,
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_underone_visited_exclude_bfunknown, Indicator.SUM),
            Indicator('% Under 1 Upto Date Immunization',\
                self.perc_uptodate_immunization, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_underone_exclude_imm_unknown, Indicator.SUM),
            Indicator('% 6m-59m with MUAC < 125',\
                self.perc_muac_below125, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]',\
                self.num_nutrition_rpts, Indicator.SUM),
            Indicator('# of Infant Deaths (0-11 months)',\
                self.num_infant_deaths, Indicator.SUM),
            Indicator('# of Under 5 Deaths (0-59 months)',\
                self.num_under5_deaths, Indicator.SUM),
            Indicator('# of Over 5 Deaths (0-59 months)',\
                self.num_over5_deaths, Indicator.SUM),
            Indicator('# of Under 5 with Positive RDT',\
                self.num_positive_rdts, Indicator.SUM),
            Indicator('Performance Indicators',\
                Indicator.empty_func, Indicator.empty_func),
            Indicator('% Households Visited',\
                self.perc_household_visits, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]', self.num_of_hhs, Indicator.SUM),
            Indicator('% Newborns Check-up within 7 Days of Birth',\
                self.perc_within7day_checkup, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]', self.num_births, Indicator.SUM),
            Indicator('% HHs Receiving Ontime Routine HHs Visits '\
                '(within last 90 days)', self.perc_ontime_hh_visits, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]', self.num_of_hhs, Indicator.SUM),
            Indicator('% Under-5 Receiving antimalarial/ACT Medications '\
                'with positive RDT result)', \
                self.perc_receiving_am_with_positive_rdts, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]', self.num_positive_rdts, Indicator.SUM),
            Indicator('# of Under-5 receiving ORS with reported diarrhea', \
                self.num_ors_given, Indicator.SUM),
            Indicator('# of Under-5 receiving Zinc with reported diarrhea', \
                self.num_zinc_given, Indicator.SUM),
            Indicator('% Urgent Referrals Receiving On-time Follow-Up',\
                self.perc_ontime_follow_up, \
                Indicator.AGG_PERCS, Indicator.PERC_PRINT),
            Indicator('[Denominator]', \
                self.num_of_urgent_referrals, Indicator.SUM),
            Indicator('Median number of days to follow-up referral / '\
                'treatment during "time period"', \
                self.median_number_of_followup_days, Indicator.SUM),
        ]

    def num_of_women_under50_seen(self, per_cls, per_num):
        return self._num_of_women_count(per_cls, per_num, 'women')

    def num_of_women_under50_using_fp(self, per_cls, per_num):
        return self._num_of_women_count(per_cls, per_num, 'women_using')

    def perc_of_women_under50_using_fp(self, per_cls, per_num):
        u50 = self.num_of_women_under50_seen(per_cls, per_num)
        print u50, self.num_of_women_under50_using_fp(per_cls, per_num)
        return (self.num_of_women_under50_using_fp(per_cls, per_num), u50)

    def _num_of_women_count(self, per_cls, per_num, count_str):
        if count_str not in ['women','women_using']:
            raise ValueError('Invalid aggregation string.')

        count = FamilyPlanningReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .aggregate(Sum(count_str))[count_str+'__sum']
        return 0 if count is None else count

    #
    # Pregnancy section
    #
    def pregnant_women(self, today=datetime.today().date()):
        c = []
        # Need to use Sauri specific
        # Noticed that PregnancyReport.objects.filter(encounter__chw=self)
        # does returns [], with values('encounter__patient').distinct()
        # returns some values but they are different if SPregnancy is used
        if not PregnancyReport.objects.filter():
            prgclass = SPregnancy
        else:
            prgclass = PregnancyReport
        pregs = prgclass\
            .objects\
            .filter(encounter__encounter_date__gt=today-timedelta(365.25),\
                encounter__encounter_date__lte=today)\
            .values('encounter__patient')\
            .distinct()
        print "got %d pregs" % pregs.count()

        for preg in pregs:
            patient = Patient.objects.get(pk=preg['encounter__patient'])
            pr = prgclass\
                .objects\
                .filter(encounter__patient=patient,\
                    encounter__encounter_date__lte=today,\
                    encounter__encounter_date__gt=today-timedelta(365.25))\
                .latest('encounter__encounter_date')

            # Number of days since encounter
            days = (today - pr.encounter.encounter_date.date()).days
            # Number of months since encounter
            months = round(days / 30.4375)

            print 'PR submitted %s at month %d (ago: %d)' % \
                (pr.encounter.encounter_date, pr.pregnancy_month, months)

            # If the pregnancy month plus months since encounter
            # is greater than 9 and there's no birth report,
            # then let's assume the lady is not pregnant
            months_pregnant = pr.pregnancy_month + months
            if months_pregnant > 9:
                print 'too old %d in %s' % \
                    (pr.pregnancy_month, pr.encounter.encounter_date)
                continue

            # Look for a baby since the pregnancy
            b = Patient\
                .objects\
                .filter(mother__pk=pr.encounter.patient.pk,\
                    dob__gte=today-timedelta(months_pregnant*30.4375),\
                    dob__lte=today)

            # If the birthreport has been found, then she's no longer
            # pregnant
            if b.count() > 0:
                print 'birth at %d' % months_pregnant
                continue

            # Look for a stillbirth/miscarriage
            s = StillbirthMiscarriageReport\
                .objects\
                .filter(encounter__patient__pk=pr.encounter.patient.pk,\
                    incident_date__gte=\
                        today-timedelta(months_pregnant*30.4375),\
                    incident_date__lte=today)

            # If there was a stillbirth/misscariage, then she's
            # no longer pregnant
            if s.count() > 0:
                print 'stillbirth'
                continue
            
            print '*PR submitted %s at month %d (ago: %d)' % \
                (pr.encounter.encounter_date, pr.pregnancy_month, months)
            c.append(patient)
        return c

    def pregnant_by_period(self, per_cls, per_num):
        return self.pregnant_women(per_cls.period_end_date(per_num))

    def num_pregnant_by_period(self, per_cls, per_num):
        return len(self.pregnant_by_period(per_cls, per_num))

    # % of women getting at least 1 ANC visit by 2nd trimester
    def perc_with_anc_second(self, per_cls, per_num):
        a, b = self._women_getting_n_anc_by(per_cls, per_num, 1, 2)
        print a, b
        return a, b

    # % of women getting at least 4 ANC visit by birth
    def perc_with_anc_four(self, per_cls, per_num):
        a, b = self._women_getting_n_anc_by(per_cls, per_num, 4, 4)
        print a, b
        return a, b

    def _women_getting_n_anc_by_tot(self, per_cls, n_anc, trimester):
        print "_women_getting_n_anc_by_tot: Trimester ", trimester
        if trimester not in xrange(1,5):
            raise ValueError('Trimester is out of range [1,4]')

        women = []
        for period in xrange(0, per_cls.num_periods):
            for w in self._women_in_month_of_preg(per_cls, per_num, trimester):
                if w not in women:
                    women.append(w)
        have_anc = filter(lambda w: w.anc_visits > n_anc, women)

        return (len(have_anc), len(women))

    def _women_getting_n_anc_by(self, per_cls, per_num, n_anc, trimester):
        print "_women_getting_n_anc_by Trimester: ", trimester
        if trimester not in xrange(1,5):
            raise ValueError('Trimester is out of range [1,4]')

        women = self._women_in_month_of_preg(per_cls, per_num, trimester)
        have_anc = filter(lambda w: w.anc_visits >= n_anc, women)

        return (len(have_anc), len(women))

    def num_women_in_second(self, per_cls, per_num):
        women = self._women_in_month_of_preg(per_cls, per_num, 2)
        return len(women)

    def num_women_in_third(self, per_cls, per_num):
        women = self._women_in_month_of_preg(per_cls, per_num, 3)
        return len(women)

    def _women_in_month_of_preg(self, per_cls, per_num, trimester):
        print "_women_in_month_of_preg Trimester: ", trimester
        if trimester not in xrange(1,5):
            raise ValueError('Trimester is out of range [1,4]')

        # e.g., 2nd trimester is range(4, 7)
        end_mo = (trimester*3)+1
        start_mo = end_mo - 3
        month_range = xrange(start_mo, end_mo)

        women = self.pregnant_by_period(per_cls, per_num)

        # Get latest pregnancy report for woman
        preggers = []
        for w in women:
            try:
                rpt = PregnancyReport\
                        .objects\
                        .filter(encounter__patient=w, \
                            encounter__encounter_date__gte=\
                                per_cls.period_start_date(per_num) - \
                                    timedelta(30.4375 * 10))\
                        .latest('encounter__encounter_date')
            except PregnancyReport.DoesNotExist:
                continue
            preggers.append(rpt)
        
        # See how many women fall in this trimester
        targets = []
        for p in preggers:
            days_ago = (per_cls.period_end_date(per_num) - \
                p.encounter.encounter_date.date()).days
            months_ago = days_ago / 30.4375
            months_of_preg = p.pregnancy_month + months_ago

            if round(months_of_preg) in month_range:
                targets.append(p)

        return targets

    def _births(self, per_cls, per_num):
        return BirthReport\
            .indicators\
            .for_period(per_cls, per_num)\

    def num_births(self, per_cls, per_num):
        return self._births(per_cls, per_num).count()

    def num_births_delivered_in_facility(self, per_cls, per_num):
        return self._births(per_cls, per_num)\
            .filter(clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def perc_births_delivered_in_facility(self, per_cls, per_num):
        print 'births hf'
        return self.num_births_delivered_in_facility(\
                per_cls, per_num), \
            self.num_births(per_cls, per_num)

    def _births_with_low_weight(self, per_cls, per_num):
        return self._births_delivered_in_facility(per_cls, per_num)\
            .filter(weight__lt=2.5)

    def _births_delivered_in_facility(self, per_cls, per_num):
        return  self._births(per_cls, per_num)\
            .filter(clinic_delivery=BirthReport.CLINIC_DELIVERY_YES)

    def num_births_with_low_weight(self, per_cls, per_num):
        return self._births_with_low_weight(per_cls, per_num).count()

    def num_births_delivered_in_facility(self, per_cls, per_num):
        return self._births_delivered_in_facility(per_cls, per_num).count()

    def perc_births_with_low_weight(self, per_cls, per_num):
        print "births lw"
        return self.num_births_with_low_weight(per_cls, per_num), \
            self.num_births_delivered_in_facility(per_cls, per_num)

    def _underone_visited(self, per_cls, per_num):
        return UnderOneReport\
            .indicators\
            .for_period(per_cls, per_num)

    def num_underone_exclusively_bf(self, per_cls, per_num):
        return self._underone_visited(per_cls, per_num)\
            .filter(breast_only=UnderOneReport.BREAST_YES)\
            .values('encounter__patient')\
            .distinct().count()

    def num_underone_visited_exclude_bfunknown(self, per_cls, per_num):
        return self._underone_visited(per_cls, per_num)\
            .exclude(breast_only=UnderOneReport.BREAST_UNKOWN)\
            .values('encounter__patient')\
            .distinct().count()

    def perc_underone_exclusively_bf(self, per_cls, per_num):
        print "underone ebf"
        return self.num_underone_exclusively_bf(per_cls, per_num), \
            self.num_underone_visited_exclude_bfunknown(per_cls, per_num)

    def num_uptodate_immunization(self, per_cls, per_num):
        return self._underone_visited(per_cls, per_num)\
            .filter(immunized=UnderOneReport.IMMUNIZED_YES)\
            .count()

    def perc_uptodate_immunization(self, per_cls, per_num):
        print "uptodate imm"
        return self.num_uptodate_immunization(per_cls, per_num), \
            self.num_underone_exclude_imm_unknown(per_cls, per_num)

    def num_underone_exclude_imm_unknown(self, per_cls, per_num):
        return self._underone_visited(per_cls, per_num)\
                .exclude(immunized=UnderOneReport.IMMUNIZED_UNKOWN)\
                .count()

    def _6mto59m_patients(self, per_cls, per_num):
        _6m_ago, _59m_ago = self._6mto59m_dates(per_cls, per_num)
        return Patient.objects.filter(dob__lt=_6m_ago, \
            dob__gt=_59m_ago)

    def _6mto59m_dates(self, per_cls, per_num):
        _6m_ago = per_cls.period_start_date(per_num) + relativedelta(months=-6)
        _59m_ago = per_cls.period_start_date(per_num) + \
            relativedelta(months=-59)
        return _6m_ago, _59m_ago

    def _nutrition_rpts(self, per_cls, per_num):
        _6m_ago, _59m_ago = self._6mto59m_dates(per_cls, per_num)
        return NutritionReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .filter(encounter__patient__dob__lt=_6m_ago, \
                encounter__patient__dob__gt=_59m_ago)

    def num_muac_below125(self, per_cls, per_num):
        return self._nutrition_rpts(per_cls, per_num)\
            .filter(muac__lt=125)\
            .values('encounter__patient')\
            .distinct()\
            .count()

    def perc_muac_below125(self, per_cls, per_num):
        print "muac below"
        return self.num_muac_below125(per_cls, per_num), \
            self.num_nutrition_rpts(per_cls, per_num)

    def num_nutrition_rpts(self, per_cls, per_num):
        return self._nutrition_rpts(per_cls, per_num)\
                .values('encounter__patient')\
                .distinct()\
                .count()

    def _deaths(self, per_cls, per_num):
        return DeathReport\
            .indicators\
            .for_period(per_cls, per_num)

    def num_infant_deaths(self, per_cls, per_num):
        print "infant"
        cur_period = per_cls.period_end_date(per_num)
        _11m = cur_period + relativedelta(months=-11)
        return self._deaths(per_cls, per_num)\
            .filter(encounter__patient__dob__gt=_11m, \
                encounter__patient__dob__lt=cur_period)\
            .count()

    def num_under5_deaths(self, per_cls, per_num):
        print "under5"
        cur_period = per_cls.period_end_date(per_num)
        _59m = cur_period + relativedelta(months=-59)
        return self._deaths(per_cls, per_num)\
            .filter(encounter__patient__dob__gt=_59m, \
                encounter__patient__dob__lt=cur_period)\
            .count()

    def num_over5_deaths(self, per_cls, per_num):
        print "over5"
        cur_period = per_cls.period_end_date(per_num)
        _59m = cur_period + relativedelta(months=-59)
        return self._deaths(per_cls, per_num)\
            .filter(encounter__patient__dob__lt=_59m)\
            .count()

    def num_tested_rdts(self, per_cls, per_num):
        return FeverReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .exclude(rdt_result=FeverReport.RDT_UNKOWN)\
            .count()

    def num_positive_rdts(self, per_cls, per_num):
        return FeverReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .filter(rdt_result=FeverReport.RDT_POSITIVE)\
            .count()

    def num_receiving_am_with_positive_rdts(self, per_cls, per_num):
        c = 0
        for r in MedicineGivenReport.indicators.for_period(per_cls, per_num):
            if FeverReport.objects.filter(encounter=r.encounter, \
                rdt_result=FeverReport.RDT_POSITIVE):
                c += 1
        return 0

    def perc_receiving_am_with_positive_rdts(self, per_cls, per_num):
        return self.num_receiving_am_with_positive_rdts(per_cls, per_num), \
            self.num_positive_rdts(per_cls, per_num)

    #
    # HH Visit section
    #

    def households(self, today=None):
        '''
        List of households
        '''
        p = Patient.objects.filter(health_id=F('household__health_id'), \
                status=Patient.STATUS_ACTIVE)
        if today is None:
            return p
        else:
            return p.filter(created_on__lte=today)

    def num_of_hhs(self, per_cls, per_num):
        return self.households(\
            per_cls.period_end_date(per_num)).count()

    def num_of_hh_visits(self, per_cls, per_num):
        return HouseholdVisitReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .values('encounter__patient')\
            .distinct()\
            .count()

    def num_of_hh_visits_in_90days(self, per_cls, per_num):
        _end_date = per_cls.period_end_date(per_num)
        _start_date = _end_date + relativedelta(days=-90)
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__encounter_date__gte=_start_date, \
                encounter__encounter_date__lte=_end_date)\
            .values('encounter__patient')\
            .distinct()\
            .count()

    def perc_ontime_hh_visits(self, per_cls, per_num):
        return self.num_of_hh_visits_in_90days(per_cls, per_num), \
            self.num_of_hhs(per_cls, per_num)

    def perc_household_visits(self, per_cls, per_num):
        return self.num_of_hh_visits(per_cls, per_num), \
            self.num_of_hhs(per_cls, per_num)

    def num_ontime_muac(self, per_cls, per_num):
        # patients due for muac received their last muac more than 75 days b4
        # at the start of time period, or do have reached 6 months and are due
        # for their muac visit
        muac_patients = self._6mto59m_patients(per_cls, per_num)
        pass

    def _within7day_checkup(self, report):
        '''report - NeonatalReport instance'''
        if not isinstance(report, NeonatalReport):
            raise ValueError("Report is not a Neonatal Report!")
        try:
            br = BirthReport\
                .objects\
                .filter(encounter__patient=report.encounter.patient)\
                .latest()
        except BirthReport.DoesNotExist:
            return False
        tdiff = (report.encounter.encounter_date - \
            br.encounter.encounter_date).days
        if tdiff >= 0 and tdiff <= 7:
            return True
        return False

    def num_of_within7day_checkup(self, per_cls, per_num):
        c = 0
        for report in NeonatalReport.indicators.for_period(per_cls, per_num):
            if self._within7day_checkup(report):
                c += 1
        return c

    def perc_within7day_checkup(self, per_cls, per_num):
        return self.num_of_within7day_checkup(per_cls, per_num), \
            self.num_births(per_cls, per_num)

    def num_diarrhea(self, per_cls, per_num):
        return DangerSignsReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .filter(danger_signs__code='dr')\
            .count()

    def num_ors_given(self, per_cls, per_num):
        return MedicineGivenReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .filter(medicines__code='r')\
            .count()

    def num_zinc_given(self, per_cls, per_num):
        return MedicineGivenReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .filter(medicines__code='z')\
            .count()

    def num_ontime_follow_up(self, per_cls, per_num):
        count = 0
        for r in ReferralReport\
            .indicators\
            .for_period(per_cls, per_num):

            due_by = r.encounter.encounter_date + timedelta(3)
            f = FollowUpReport\
                .indicators\
                .filter(encounter__patient__pk=r.encounter.patient.pk,\
                    encounter__encounter_date__lte=due_by,
                    encounter__encounter_date__gt=\
                        r.encounter.encounter_date)\
                .count()

            if f is None or f == 0:
                continue
            else:
                count += 1
        return count

    def num_of_urgent_referrals(self, per_cls, per_num):
        return ReferralReport\
            .indicators\
            .for_period(per_cls, per_num)\
            .filter(urgency__in=(ReferralReport.URGENCY_AMBULANCE, \
                ReferralReport.URGENCY_EMERGENCY, \
                ReferralReport.URGENCY_BASIC))\
            .values('encounter__patient')\
            .distinct()\
            .count()

    def perc_ontime_follow_up(self, per_cls, per_num):
        return self.num_ontime_follow_up(per_cls, per_num), \
            self.num_of_urgent_referrals(per_cls, per_num)

    def median_number_of_followup_days(self, per_cls, per_num):
        referrals = ReferralReport\
            .indicators\
            .for_period(per_cls, per_num)
        lsdays = []
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            fur = FollowUpReport\
                .objects\
                .filter(encounter__patient=referral.encounter.patient, \
                    encounter__encounter_date__gt=rdate)\
                .order_by('encounter__encounter_date')
            if fur:
                fdate = fur[0].encounter.encounter_date
                lsdays.append((fdate - rdate).days)
        if not lsdays:
            return ''
        return int(get_median(lsdays))
