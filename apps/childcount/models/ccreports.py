#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import gettext as _
from django.db.models import F

from datetime import date, timedelta, datetime

from childcount.models import Patient
from locations.models import Location
from childcount.models import CHW, Clinic
from childcount.models import NutritionReport, FeverReport, ReferralReport
from childcount.models import BirthReport, PregnancyReport
from childcount.models import HouseholdVisitReport, FollowUpReport
from childcount.models import ImmunizationSchedule, ImmunizationNotification
from childcount.models import BedNetReport, BednetUtilization, \
                                        BednetIssuedReport

from childcount.utils import day_end, day_start, get_dates_of_the_week, \
                                get_median, seven_days_to_date, \
                                first_day_of_month, last_day_of_month

from logger.models import IncomingMessage, OutgoingMessage


class ThePatient(Patient):

    class Meta:
        verbose_name = _("Patient List Report")
        proxy = True

    def latest_muac(self):
        muac = NutritionReport.objects.filter(encounter__patient=self).latest()
        if not None:
            return u"%smm %s" % (muac.muac, muac.verbose_state)
        return u""

    def check_visit_within_seven_days_of_birth(self):
        seven_days_after_birth = self.dob + timedelta(7)
        hvr = HouseholdVisitReport.objects\
                .filter(encounter__encounter_date__gt=self.dob, \
                    encounter__encounter_date__lte=seven_days_after_birth)\
                .count()
        if hvr:
            return True
        else:
            return False

    def visit_within_90_days_of_last_visit(self):
        try:
            hvr = HouseholdVisitReport.objects\
                        .filter(encounter__patient=self.household).latest()
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

    def ontime_muac(self):
        try:
            nr = NutritionReport.objects\
                    .filter(encounter__patient=self).latest()
            latest_date = nr.encounter.encounter_date
            old_date = latest_date - timedelta(90)
            nr = NutritionReport.objects.filter(encounter__patient=self, \
                                encounter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if nr.count():
                return True
            return False
        except NutritionReport.DoesNotExist:
            return False

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
                    notify_on = patient_dob + timedelta(30.4375 * period.period)
                    immunization.notify_on = notify_on

                immunization.save()

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
            'bit': '{{object.last_name}} {{object.first_name}}'})
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

    def patient_register_columns(cls):
        columns = []
        columns.append(
            {'name': _(u"HHID"), \
            'bit': '{{object.health_id.upper}}'})
        columns.append(
            {'name': _(u"Name".upper()), \
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': cls._meta.get_field('gender').verbose_name.upper(), \
            'bit': '{{object.gender}}'})
        columns.append(
            {'name': _(u"Age".upper()), \
            'bit': '{{object.humanised_age}}'})
        columns.append(
            {'name': _(u"Status".upper()), \
            'bit': '{{object.status_text}}'})
        columns.append(
            {'name': _(u"HHID".upper()), \
            'bit': '{{object.household.health_id.upper}}'})
        return columns


class TheCHWReport(CHW):

    class Meta:
        verbose_name = _("Community Health Worker Report")
        proxy = True

    @property
    def num_of_patients(self):
        num = Patient.objects.filter(chw=self).count()
        return num

    @property
    def num_of_underfive(self):
        return self.patients_under_five().count()

    def patients_under_five(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        return Patient.objects.filter(chw=self, dob__lte=sixtym)

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
                                status=NutritionReport.STATUS_MODERATE).count()
        return num

    def mam_cases(self, startDate=None, endDate=None):
        return NutritionReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def severe_mam_cases(self, startDate=None, endDate=None):
        num = NutritionReport.objects.filter(encounter__chw=self, \
                            status=NutritionReport.STATUS_SEVERE_COMP, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        num += NutritionReport.objects.filter(encounter__chw=self, \
                                status=NutritionReport.STATUS_SEVERE, \
                            encounter__encounter_date__gte=startDate, \
                            encounter__encounter_date__lte=endDate).count()
        return num

    @property
    def num_of_healthy(self):
        num = NutritionReport.objects.filter(created_by=self, \
                                status=NutritionReport.STATUS_HEALTHY).count()
        return num

    @property
    def num_of_visits(self):
        '''The number of visits in the last 7 days'''
        seven = date.today() - timedelta(7)
        #num = HouseholdVisitReport.objects.filter(created_by=self).count()
        return 2

    @property
    def num_muac_eligible(self):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(chw=self, dob__gte=sixtym, \
                                     dob__lte=sixm).count()
        return num

    @classmethod
    def total_muac_eligible(cls):
        sixtym = date.today() - timedelta(int(30.4375 * 59))
        sixm = date.today() - timedelta(int(30.4375 * 6))
        num = Patient.objects.filter(dob__gte=sixtym, \
                                     dob__lte=sixm).count()
        return num

    @property
    def num_of_sms(self):
        identity = self.connection().identity
        num = IncomingMessage.objects.filter(identity=identity).count()
        return num

    @property
    def number_of_households(self):
        return self.households().count()

    def households(self):
        return Patient.objects.filter(health_id=F('household__health_id'), \
                                        chw=self)

    def num_of_householdvisits(self):
        return HouseholdVisitReport.objects.filter(encounter__chw=self).count()

    def household_visit(self, startDate=None, endDate=None):
        return HouseholdVisitReport.objects.filter(encounter__chw=self, \
                                encounter__encounter_date__gte=startDate, \
                                encounter__encounter_date__lte=endDate).count()

    def percentage_ontime_visits(self):
        households = self.households()
        num_on_time = 0
        for household in households:
            thepatient = ThePatient.objects.get(health_id=household.health_id)
            if thepatient.visit_within_90_days_of_last_visit():
                num_on_time += 1
        if num_on_time is 0:
            return 0
        else:
            total_households = households.count()
            return int(round((num_on_time / float(total_households)) * 100))

    def num_of_births(self):
        return BirthReport.objects.filter(encounter__chw=self).count()

    def percentage_ontime_birth_visits(self):
        births = BirthReport.objects.filter(encounter__chw=self)
        count = 0
        for birth in births:
            thepatient = ThePatient.objects.get(id=birth.encounter.patient)
            if thepatient.check_visit_within_seven_days_of_birth():
                count += 1
        if not count:
            return count
        return int(round(100 * (count / float(births.count()))))

    def num_of_clinic_delivery(self):
        return BirthReport.objects.filter(encounter__chw=self, \
                        clinic_delivery=BirthReport.CLINIC_DELIVERY_YES).count()

    def percentage_clinic_deliveries(self):
        num_of_clinic_delivery = self.num_of_clinic_delivery()
        num_of_births = self.num_of_births()
        if num_of_births == 0:
            return 0
        return int(round(num_of_clinic_delivery / float(num_of_births)) * 100)

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
        underfives = self.patients_under_five()
        count = 0
        for achild in underfives:
            thepatient = ThePatient.objects.get(id=achild.id)
            if thepatient.ontime_muac():
                count += 1
        if not count:
            return count
        else:
            total_count = underfives.count()
            return int(round(100 * (count / float(total_count))))

    def num_of_active_sam_cases(self):
        count = 0
        danger = (NutritionReport.STATUS_SEVERE, \
                        NutritionReport.STATUS_SEVERE_COMP)
        nr = NutritionReport.objects\
                        .filter(encounter__chw=self, status__in=danger)\
                        .values('encounter__patient').distinct()
        for r in nr:
            p = Patient.objects.get(id=r['encounter__patient'])
            latest = NutritionReport.objects.filter(encounter__patient=p)\
                                            .latest()
            if latest.status in danger:
                count += 1
        return count

    def num_of_pregnant_women(self):
        return len(self.pregnant_women())

    def pregnant_women(self):
        c = []
        pregs = PregnancyReport.objects.filter(encounter__chw=self)\
                                .values('encounter__patient').distinct()
        for preg in pregs:
            patient = Patient.objects.get(id=preg['encounter__patient'])
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            days = (pr.encounter.encounter_date - datetime.now()).days
            months = round(days / 30.4375)
            if pr.pregnancy_month + months < 9:
                c.append(patient)
        return c

    def num_pregnant_refferred(self):
        pwomen = self.pregnant_women()
        rr = ReferralReport.objects.filter(encounter__patient__in=pwomen, \
                                        encounter__chw=self)
        return rr.count()

    def percentage_pregnant_ontime_visits(self):
        pwomen = self.pregnant_women()
        count = 0
        for patient in pwomen:
            pr = PregnancyReport.objects.filter(encounter__patient=patient)\
                                        .latest()
            latest_date = pr.encounter.encounter_date
            old_date = latest_date - timedelta(6 * 7)
            pr = PregnancyReport.objects.filter(encounter__patient=patient, \
                                encounter__encounter_date__gte=old_date, \
                                encounter__encounter_date__lt=latest_date)
            if pr.count():
                count += 1
        if not count:
            return count
        else:
            total_count = len(pwomen)
            return int(round(100 * (count / float(total_count))))

    def percentage_ontime_followup(self):
        referrals = ReferralReport.objects.filter(encounter__chw=self)
        if not referrals:
            return ''
        num_referrals = referrals.count()
        ontimefollowup = 0
        for referral in referrals:
            rdate = referral.encounter.encounter_date
            day2later = day_end(rdate + timedelta(2))
            fur = FollowUpReport.objects.filter(encounter__chw=self, \
                            encounter__patient=referral.encounter.patient, \
                            encounter__encounter_date__gt=rdate, \
                            encounter__encounter_date__lte=day2later)
            if fur:
                ontimefollowup += 1
        return '%s%%' % int(round((ontimefollowup / \
                        float(num_referrals)) * 100))

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
            return 0
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
        return (now - last_sms[0].received).days

    def activity_summary(self):
        today = datetime.today()
        startDate = today - timedelta(today.weekday())
        p = {}

        p['sdate'] = startDate.day
        p['edate'] = today.day
        p['severemuac'] = self.severe_mam_cases(startDate=startDate, \
                            endDate=today)
        p['numhvisit'] = self.household_visit(startDate=startDate, \
                            endDate=today)
        p['muac'] = self.mam_cases(startDate=startDate, endDate=today)
        p['rdt'] = self.rdt_cases(startDate=startDate, endDate=today)
        p['household'] = self.number_of_households
        p['tclient'] = self.num_of_patients
        p['ufive'] = self.num_of_underfive

        return p

  
    def num_of_bednetsurvey(self):
        return BedNetReport.objects.filter(encounter__chw=self).count()

    def per_bednetsurvey(self):
        household = BedNetReport.objects.filter(encounter__chw=self).count()
        survey = self.number_of_households()
        ans = int(round((household / float(survey)) * 100))
        return household

    def num_sleepingsite(self):
        survey = BedNetReport.objects.filter(encounter__chw=self)
        total = 0
        for s in survey:
            total += s.sleeping_sites
        return total

    def num_damaged(self):
        survey = BedNetReport.objects.filter(encounter__chw=self)
        total = 0
        for s in survey:
            total += s.damaged_nets
        return total

    def num_earlier(self): 
        survey = BedNetReport.objects.filter(encounter__chw=self)
        total = 0
        for s in survey:
            total += s.earlier_nets
        return total

    def num_funcbednet(self): 
        survey = BedNetReport.objects.filter(encounter__chw=self)
        total = 0
        for s in survey:
            total += s.function_nets
        return total

    def required_bednet(self):
        total = self.num_sleepingsite() - self.num_funcbednet()
        return total

    @classmethod
    def muac_summary(cls):
        num_healthy = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_HEALTHY).count()
        num_mam = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_MODERATE).count()
        num_sam = NutritionReport.objects.filter(\
                        status=NutritionReport.STATUS_SEVERE).count()
        num_comp = NutritionReport.objects.filter(\
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
             'bit': '{{ object.location }}'})
        columns.append(
            {'name': _("Name".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name': "No. of House holds".upper(), \
             'bit': '{{ object.number_of_households}}'})
        columns.append(
            {'name': "Household Survey Done".upper(), \
             'bit': '{{ object.num_of_bednetsurvey}}'})
        columns.append(
            {'name': "Percentage".upper(), \
             'bit': '{{ object.per_bednetsurvey}}'})
        columns.append(
            {'name': "Total Sleeping site".upper(), \
             'bit': '{{ object.num_sleepingsite}}'})
        columns.append(
            {'name': "Functioning Bednet".upper(), \
             'bit': '{{ object.num_funcbednet}}'})
        columns.append(
            {'name': "Damaged Bednet".upper(), \
             'bit': '{{ object.num_damaged}}'})
        columns.append(
            {'name': "Earlier(b4 2009)".upper(), \
             'bit': '{{ object.num_earlier}}'})
        columns.append(
            {'name': "Required Bednet".upper(), \
             'bit': '{{ object.required_bednet}}'})
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
        columns = []
        columns.append({'name': _("CHW"), 'bit': '{{object}}'})
        columns.append({'name': _("# of Households"), \
                'bit': '{{object.number_of_households}}'})
        columns.append({'name': _("# of Household Visits"), \
                'bit': '{{object.num_of_householdvisits}}'})
        columns.append({'name': _("% of HHs receiving on-time routine visit "\
                                    "(within 90 days) [S23]"), \
                'bit': '{{object.percentage_ontime_visits}}%'})
        columns.append({'name': _("# of Births"), \
                'bit': '{{object.num_of_births}}'})
        columns.append({'name': _("% Births delivered in "\
                                    "Health Facility [S4]"),
                'bit': '{{object.percentage_clinic_deliveries}}%'})
        columns.append({'name': _("% Newborns checked within 7 days of birth "\
                            "[S6]"), \
                'bit': '{{object.percentage_ontime_birth_visits}}%'})
        columns.append({'name': _("# of Under-5s"), \
                'bit': '{{object.num_of_underfive}}'})
        columns.append({'name': _("# Under-5 Referred for Danger Signs"), \
                'bit': '{{object.num_underfive_refferred}}'})
        columns.append({'name': _("# Under-5 Treated for Malarias"), \
                'bit': '{{object.num_underfive_malaria}}'})
        columns.append({'name': _("# Under-5 Treated for Diarrhea"), \
                'bit': '{{object.num_underfive_diarrhea}}'})
        columns.append({'name': _("% Under-5 receiving on-time MUAC "\
                                    "(within 90 days) [S11]"), \
                'bit': '{{object.percentage_ontime_muac}}%'})
        columns.append({'name': _("# of Active SAM cases"), \
                'bit': '{{object.num_of_active_sam_cases}}'})
        columns.append({'name': _("# of Pregnant Women"), \
                'bit': '{{object.num_of_pregnant_women}}'})
        columns.append({'name': _("# Pregnant Women Referred for "\
                                    "Danger Signs"),
                'bit': '{{object.num_pregnant_refferred}}'})
        columns.append({'name': _("% Pregnant receiving on-time visit"\
                        " (within 6 weeks) [S24]"), \
                'bit': '{{object.percentage_pregnant_ontime_visits}}'})
        columns.append({'name': _("% Referred / Treated receiving on-time "\
                                    "follow-up (within 2 days) [S13]"),
                'bit': '{{object.percentage_ontime_followup}}'})
        columns.append({'name': _("Median # of days for follow-up [S25]"), \
                'bit': '{{object.median_number_of_followup_days}}'})
        columns.append({'name': _("SMS Error Rate %"),
                'bit': '{{object.sms_error_rate}}%'})
        columns.append({'name': _("Days since last SMS transmission"), \
                'bit': '{{object.days_since_last_sms}}'})
        self.columns = columns

    def get_columns(self):
        return self.columns


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
    def summary(cls):
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
                            status=NutritionReport.STATUS_SEVERE_COMP).count()
        num += NutritionReport.objects.filter(\
                                status=NutritionReport.STATUS_SEVERE).count()

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
