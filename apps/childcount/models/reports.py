#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin, ukanga

"""ChildCount Reports"""

import calendar
from datetime import datetime
from datetime import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from celery.decorators import task
from celery.registry import tasks
from celery.task.control import revoke

from django.db import models
from django.db import connection
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _
import reversion
from reversion.models import Version

from polymorphic import PolymorphicModel, PolymorphicManager
from polymorphic import PolymorphicQuerySet

from mgvmrs.forms import OpenMRSHouseholdForm, OpenMRSConsultationForm

from alerts.utils import SmsAlert
from alerts.models import SmsAlertModel

from childcount.models import Patient
from childcount.models import Encounter
from childcount.models import Vaccine

from childcount.utils import send_msg

class AgeQuerySet(PolymorphicQuerySet):
    """For filtering on age at time of encounter
    
    This custom SQL allows us easily to filter to find
    CCReports that were recorded when the patient was between
    START and END days old (inclusive).

    The Django way to do this would be to use and :class:`django.db.models.F()` + 
    :class:`datetime.timedelta()`
    in a :meth:`.filter()` call, but that operation isn't supported in
    Django 1.1.
    """

    def encounter_under_five(self):
        """Anyone under 365*5 days old at time of encounter"""
        return self.encounter_age(0, 365.25*5)
   
    def encounter_over_five(self):
        """We take anyone between five and 200 years old to be
        "over five"
        """
        return self.encounter_age((365.25*5)+0.25, 365.25*200)
    
    def encounter_muac_eligible(self):
        """MUAC eligible kids are 6 months - 5 years old"""
        return self.encounter_age(180, 365.25*5)
   
    def _encounter_filter_sql(self, query):
        """Helper function for filtering the CCReport QuerySet
        by a custom SQL call on Encounters.

        query - An SQL query string containing %(pks_str)s 
                into which the list of the input QuerySet's
                encounter primary keys will be inserted.
        """
        if self.count() == 0:
            return self

        # Get distinct encounters
        encs = self.values_list('encounter__pk').distinct()

        # Turn them into a list of pk strings
        pks_encounter = [str(x[0]) for x in encs]

        # Join into a comma-separated string
        pks_str = ','.join(pks_encounter)

        # Run query
        cursor = connection.cursor()
        cursor.execute(query % {'pks_str': pks_str})

        # Convert back into a list of pks
        pks = [x[0] for x in cursor.fetchall()]

        # Return the input QuerySet filtered by relevant encounter
        return self.filter(encounter__pk__in=pks)

    """
    This version of encounter_age is cleaner code-wise but
    runs 10-20 times slower than the pure SQL version below.

    def encounter_age(self, min_days, max_days):
        # Make sure we have a float
        min_days = float(min_days)
        max_days = float(max_days)

        return self\
            .filter(encounter__encounter_date__isnull=False,\
                encounter__patient__dob__isnull=False)\
            .extra(where=["DATEDIFF(`cc_encounter`.`encounter_date`, `cc_patient`.`dob`) BETWEEN %s AND %s"],\
                    params=[min_days, max_days])
    """

    def encounter_age(self, min_days, max_days):
        """Anyone who is between `min_days` and `max_days`
        old (inclusive)
        """

        q = \
        '''
        SELECT  `cc_encounter`.`id`
        FROM    `cc_encounter`

        LEFT JOIN `cc_patient` ON 
            (`cc_encounter`.`patient_id`=`cc_patient`.`id`)

        WHERE
            DATEDIFF(`cc_encounter`.`encounter_date`, `cc_patient`.`dob`)
                BETWEEN "%(min_days)d" AND "%(max_days)d" AND
             `cc_encounter`.`id` IN (%(pks_str)s);
        ''' % {'min_days': min_days, 
                'max_days': max_days,
                'pks_str': "%(pks_str)s"}

        return self._encounter_filter_sql(q)

    def latest_for_patient(self):
        """:meth:`latest_for_patient` filters the :class:`CCReport` QuerySet
        and returns only :class:`CCReport` objects that are the latest such
        report for each patient.

        For example, if you had a QuerySet of :class:`HouseholdVisitReport`
        objects, :meth:`latest_for_patient` would give you the most
        recent :class:`HouseholdVisitReport` for each household.
        """

        q = """
        SELECT `cc_encounter`.`id`

        FROM `cc_encounter`

        LEFT JOIN `cc_encounter` AS `cc_encounter2`
            ON (`cc_encounter`.`patient_id` = `cc_encounter2`.`patient_id` AND
                `cc_encounter`.`encounter_date` < `cc_encounter2`.`encounter_date` AND
                `cc_encounter2`.`id` IN (%(pks_str)s))

        WHERE 
            `cc_encounter`.`id` IN (%(pks_str)s) AND
            `cc_encounter2`.`id` IS NULL

        GROUP BY
            `cc_encounter`.`patient_id`
        """

        return self._encounter_filter_sql(q)
    
    def __hash__(self):
        """Define a hash function that depends only on the pks of the
        rows in the QuerySet
        """
        return hash((self.model,) + tuple(self.order_by('pk').values_list('pk')))

class CCReport(PolymorphicModel):
    """The highest level superclass to be 
    inhereted by all other report classes
    """

    objects = PolymorphicManager(AgeQuerySet)

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_ccrpt'
        verbose_name = _(u"ChildCount Report")
        verbose_name_plural = _(u"ChildCount Reports")
        get_latest_by = ('encounter__encounter_date')

    encounter = models.ForeignKey(Encounter, verbose_name=_(u"Encounter"))

    def substantively_equal(self, other):
        """Two :class:`childcount.models.reports.CCReport` objects are of the same
        type and have all fields equal (except for their
        `id`)
        """

        if type(self) != type(other):
            return False

        for f in self._meta.fields:
            fname = f.name
            if fname in ['id', 'ccreport_ptr']:
                continue

            v1 = getattr(self, fname)
            v2 = getattr(other, fname)
            if v1 != v2: return False

        return True

    def reset(self):
        """Zero out the report"""
        self.__init__(pk=self.pk, encounter=self.encounter)

    def patient(self):
        return self.encounter.patient

    def chw(self):
        return self.encounter.chw

    def initial_version(self):
        return Version.objects.get_for_object(self)[0]

    def current_version(self):
        return Version.objects.get_for_object(self).\
                                      order_by('-revision__date_created')[0]

    def entered_by(self):
        return self.initial_version().revision.user

    def entered_on(self):
        return self.initial_version().revision.date_created

    def modified(self):
        return Version.objects.get_for_object(self).count() > 1

    def modified_by(self):
        if not self.modified():
            return None
        return self.current_version().revision.user

    def modified_on(self):
        if not self.modified():
            return None
        return self.current_version().revision.date_created

    def __unicode__(self):
        string = u"%s %s" % (self.encounter, self._meta.verbose_name)
        try:
            string += " - %s" % self.summary()
        except AttributeError:
            pass
        return string

    def get_omrs_dict(self):
        """OpenMRS Key/Value dict.

        Return key/value dictionary of openmrs values that this report can
        populate
        """
        return {}

    def identity(self):
        return self.chw().connection().identity

reversion.register(CCReport)


class BirthReport(CCReport):
    """Birth Report"""

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_birthrpt'
        verbose_name = _(u"Birth Report")
        verbose_name_plural = _(u"Birth Reports")

    CLINIC_DELIVERY_YES = 'Y'
    CLINIC_DELIVERY_NO = 'N'
    CLINIC_DELIVERY_UNKNOWN = 'U'
    CLINIC_DELIVERY_CHOICES = (
        (CLINIC_DELIVERY_YES, _(u"Yes")),
        (CLINIC_DELIVERY_NO, _(u"No")),
        (CLINIC_DELIVERY_UNKNOWN, _(u"Unknown")))
    """Whether or not the baby was delivered in a clinic"""

    clinic_delivery = models.CharField(_(u"Clinic delivery"), max_length=1, \
                                       choices=CLINIC_DELIVERY_CHOICES, \
                                       help_text=_(u"Was the baby born in " \
                                                    "a health facility?"),\
                                        db_index=True)

    weight = models.FloatField(_(u"Birth weight (kg)"), null=True, blank=True,\
                                        db_index=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('clinic_delivery')[0].verbose_name, \
             self.get_clinic_delivery_display())
        if self.weight:
            string += ", %s: %s" % \
                    (self._meta.get_field_by_name('weight')[0].verbose_name, \
                     self.weight)
        return string

    def get_omrs_dict(self):
        igive = {}
        if self.weight:
            igive.update({'weight': self.weight})
        return igive

    @task()
    def initial_neonatal_visit_reminder(self):
        """Six days after a birth report remind the CHW to do an initial neonatal
        visit if it has not been done yet.
        """
        try:
            self = BirthReport.objects.get(pk=self.pk)
        except BirthReport.DoesNotExist:
            pass
        else:
            nr = NeonatalReport.objects.filter(\
                                encounter__patient=self.encounter.patient)
            nr_msg = _(u"+N")
            if nr:
                nr_msg = u""
            ur = UnderOneReport.objects.filter(\
                                encounter__patient=self.encounter.patient)
            ur_msg = _(u"+T")
            if ur:
                ur_msg = u""

            if not ur or not nr:
                msg = _(u"Please make sure %(child)s gets their Initial"\
                        " Neonatal Visit [%(forms)s]") % {
                        'child': self.encounter.patient,
                        'forms': ' ' . join([nr_msg, ur_msg])}
                alert = SmsAlert(reporter=self.encounter.patient.chw, msg=msg)
                sms_alert = alert.send()
                sms_alert.name = u"initial_neonatal_visits_6"
                sms_alert.save()
    tasks.register(initial_neonatal_visit_reminder)

    def setup_reminders(self):
        '''
        Setup reminders for neonatal visit
            - immediate
            - 6 days later
        '''
        #immediate reminder
        msg = _(u"Please make sure %(child)s gets their initial neonatal" \
                " visit [+N and +T]") % {'child': self.encounter.patient}
        immediate_alert = SmsAlert(reporter=self.encounter.patient.chw, \
                            msg=msg)
        delay = datetime.now() + timedelta(seconds=10)
        sms_alert = immediate_alert.send(send_at=delay)
        sms_alert.name = u"initial_neonatal_visits"
        sms_alert.save()

        #six days later check if neonatal visit occured
        delay = datetime.now() + timedelta(days=6)
        result = self.initial_neonatal_visit_reminder.apply_async(eta=delay, \
                                                args=(self,))
reversion.register(BirthReport, follow=['ccreport_ptr'])


class DeathReport(CCReport):
    """Death Report"""

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_deathrpt'
        verbose_name = _(u"Death Report")
        verbose_name_plural = _(u"Death Reports")

    death_date = models.DateField(_(u"Date of death"), db_index=True)

    def summary(self):
        return u"%s: %s" % \
                (self._meta.get_field_by_name('death_date')[0].verbose_name, \
                 self.death_date)
reversion.register(DeathReport)


class StillbirthMiscarriageReport(CCReport):
    """Stillbirth/Miscarriage Report"""

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_sbmcrpt'
        verbose_name = _(u"Stillbirth / Miscarriage Report")
        verbose_name_plural = _(u"Stillbirth / Miscarriage Reports")

    TYPE_STILL_BIRTH = 'S'
    TYPE_MISCARRIAGE = 'M'
    TYPE_CHOICES = (
                       (TYPE_STILL_BIRTH, _('Stillbirth')),
                       (TYPE_MISCARRIAGE, _('Miscarriage')))

    incident_date = models.DateField(_(u"Date of stillbirth or miscarriage"),\
                            db_index=True)
    type = models.CharField(_(u"Type"), max_length=1, choices=TYPE_CHOICES,\
                            blank=True, null=True, db_index=True)

    def summary(self):
        if self.type is None:
            type = _(u"Still birth or miscarriage")
        else:
            type = self.get_type_display()
        return _(u"%(type)s on %(date)s") % \
             {'type': type, 'date': self.incident_date}

    @task()
    def chw_followup(self):
        '''
        One week after still birth remindd the chw to follow on the mother.
        '''
        try:
            self = StillbirthMiscarriageReport.objects.get(pk=self.pk)
        except StillbirthMiscarriageReport.DoesNotExist:
            pass
        else:
            condition = ''
            for x, y in self.TYPE_CHOICES:
                if x == self.type:
                    condition = y
            msg = _(u"Please do a followup on %(mother)s following her" \
                    " %(condition)s a week ago. We would expect a +U" \
                    " report.") % {
                    'mother': self.encounter.patient,
                    'condition': condition}
            alert = SmsAlert(reporter=self.encounter.chw, msg=msg)
            sms_alert = alert.send()
            sms_alert.name = u"stillbirthmiscarriage_followup"
            sms_alert.save()
    tasks.register(chw_followup)

    def setup_reminders(self):
        '''
        Setup alert/reminder to CHW one week after the event
        '''

        #One week later CHW to followup on the mother
        delay = datetime.now() + timedelta(days=7)
        #7am
        delay = datetime.combine(delay.date(), time(7, 0))
        result = self.chw_followup.apply_async(eta=delay, \
                                                args=(self,))
reversion.register(StillbirthMiscarriageReport, follow=['ccreport_ptr'])


class FollowUpReport(CCReport):
    """Follow-Up Report"""

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_furpt'
        verbose_name = _(u"Follow-up Report")
        verbose_name_plural = _(u"Follow-up Reports")

    IMPROVEMENT_YES = 'Y'
    IMPROVEMENT_NO = 'N'
    IMPROVEMENT_UNKNOWN = 'U'
    IMPROVEMENT_UNAVAILABLE = 'L'
    IMPROVEMENT_CHOICES = (
                       (IMPROVEMENT_YES, _('Yes')),
                       (IMPROVEMENT_NO, _('No')),
                       (IMPROVEMENT_UNKNOWN, _('Unkown')),
                       (IMPROVEMENT_UNAVAILABLE, _('Patient unavailable')))

    VISITED_YES = 'Y'
    VISITED_NO = 'N'
    VISITED_UNKNOWN = 'U'
    VISITED_INPATIENT = 'P'
    VISITED_CHOICES = (
                       (VISITED_YES, _('Yes')),
                       (VISITED_NO, _('No')),
                       (VISITED_UNKNOWN, _('Unkown')),
                       (VISITED_INPATIENT, _('Patient currently inpatient')))

    improvement = models.CharField(_(u"Improvement"), max_length=1, \
                                   choices=IMPROVEMENT_CHOICES, \
                              help_text=_(u"Has the patient's condition " \
                                           "improved since the last " \
                                           "CHW visit?"),\
                                db_index=True)

    visited_clinic = models.CharField(_(u"Visited clinic"), max_length=1, \
                                   choices=VISITED_CHOICES, \
                                   db_index=True,\
                              help_text=_(u"Did the patient visit a health "\
                                           "facility since the last " \
                                           "CHW visit?"))

    def summary(self):
        return u"%s: %s, %s: %s" % \
            (self._meta.get_field_by_name('improvement')[0].verbose_name, \
             self.get_improvement_display(),
             self._meta.get_field_by_name('visited_clinic')[0].verbose_name, \
             self.get_visited_clinic_display())

    def get_omrs_dict(self):

        improv_map = {
            self.IMPROVEMENT_YES: OpenMRSConsultationForm.YES,
            self.IMPROVEMENT_NO: OpenMRSConsultationForm.NO,
            self.IMPROVEMENT_UNKNOWN: OpenMRSConsultationForm.UNKNOWN,
            self.IMPROVEMENT_UNAVAILABLE: OpenMRSConsultationForm.UNAVAILABLE,
        }

        visit_map = {
            self.VISITED_YES: OpenMRSConsultationForm.YES,
            self.VISITED_NO: OpenMRSConsultationForm.NO,
            self.VISITED_UNKNOWN: OpenMRSConsultationForm.UNKNOWN,
            self.VISITED_INPATIENT: OpenMRSConsultationForm.INPATIENT,
        }

        igive = {
            'patients_condition_improved': improv_map[self.improvement],
            'visit_to_health_facility_since_last_home_visit': \
                                                visit_map[self.visited_clinic],
        }
        return igive
reversion.register(FollowUpReport, follow=['ccreport_ptr'])


class DangerSignsReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_dsrpt'
        verbose_name = _(u"Danger Signs Report")
        verbose_name_plural = _(u"Danger Signs Reports")

    danger_signs = models.ManyToManyField('CodedItem', \
                                          verbose_name=_(u"Danger Signs"))

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('danger_signs')[0].verbose_name, \
             u", ".join([ds.description for ds in self.danger_signs.all()]))

    def short_summary(self):
        return u", ".join([ds.description for ds in self.danger_signs.all()])

    def get_omrs_dict(self):
        igive = {}
        i = 0
        for ds in self.danger_signs.all():
            if i == 0:
                igive.update({'danger_signs_present': \
                                OpenMRSConsultationForm.YES})
                i = 1
                igive.update({'reasons_for_referral__regimen_failure': True})
            if ds.code.upper() == 'AS':
                igive.update({'reasons_for_referral__physical_trauma': True})
            if ds.code.upper() == 'BM':
                igive.update({'reasons_for_referral__no_fetal_movements': \
                                True})
            if ds.code.upper() == 'BV':
                igive.update({'reasons_for_referral__blurred_vision': True})
            if ds.code.upper() == 'CC':
                igive.update({'reasons_for_referral__cough': True})
            if ds.code.upper() == 'CV':
                igive.update({'reasons_for_referral__convulsions': True})
            if ds.code.upper() == 'CW':
                igive.update({'reasons_for_referral__cough_lasting_more'\
                                '_than_3_weeks': True})
            if ds.code.upper() == 'DR':
                igive.update({'reasons_for_referral__diarrhea': True})
            if ds.code.upper() == 'FP':
                igive.update({'reasons_for_referral__fever_in_first_'\
                                'trimester_of_pregnancy': True})
            if ds.code.upper() == 'NB':
                igive.update({'reasons_for_referral__night_blindness': True})
            if ds.code.upper() == 'OD':
                igive.update({'oedema': OpenMRSConsultationForm.YES})
                igive.update({'reasons_for_referral__oedema': True})
            if ds.code.upper() == 'PA':
                igive.update({'reasons_for_referral__abdominal_pain': True})
            if ds.code.upper() == 'PH':
                igive.update({'reasons_for_referral__severe_headache': True})
            if ds.code.upper() == 'PU':
                igive.update({'reasons_for_referral__dysuria': True})
            if ds.code.upper() == 'SF':
                igive.update({'reasons_for_referral__dermatitis': True})
            if ds.code.upper() == 'SW':
                igive.update({'reasons_for_referral__peripheral_edema': True})
            if ds.code.upper() == 'VB':
                igive.update({'reasons_for_referral__abnormal_vaginal_'\
                                'bleeding': True})
            if ds.code.upper() == 'VD':
                igive.update({'reasons_for_referral__vaginal_discharge': True})
            if ds.code.upper() == 'VP':
                igive.update({'reasons_for_referral__acute_vaginitis': True})
            if ds.code.upper() == 'WL':
                igive.update({'reasons_for_referral__weight_loss': True})
            if ds.code.upper() == 'NF':
                igive.update({'reasons_for_referral__unable_to_drink': True})
            if ds.code.upper() == 'Z':
                igive.update({'reasons_for_referral__other_non_coded': True})
        return igive
reversion.register(DangerSignsReport, follow=['ccreport_ptr'])


class PregnancyReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_pregrpt'
        verbose_name = _(u"Pregnancy Report")
        verbose_name_plural = _(u"Pregnancy Reports")

    pregnancy_month = models.PositiveSmallIntegerField(_(u"Months Pregnant"), \
                                    help_text=_(u"How many months into the " \
                                                 "pregnancy?"),\
                                    db_index=True)
    anc_visits = models.PositiveSmallIntegerField(_(u"ANC Visits"), \
                                    help_text=_(u"Number of antenatal clinic "\
                                                 "visits during pregnancy"),\
                                    db_index=True)
    weeks_since_anc = models.PositiveSmallIntegerField(\
                                        _(u"Weeks since last ANC visit"), \
                                        null=True, blank=True, db_index=True,\
                            help_text=_(u"How many weeks since the patient's "\
                                         "last ANC visit (0 for less " \
                                         "than 7 days)?"))

    def summary(self):
        string = u"%s: %d, %s: %d" % \
            (self._meta.get_field_by_name('pregnancy_month')[0].verbose_name, \
             self.pregnancy_month,
             self._meta.get_field_by_name('anc_visits')[0].verbose_name, \
             self.anc_visits)
        if self.weeks_since_anc:
            string += ", %s: %d" % \
            (self._meta.get_field_by_name('weeks_since_anc')[0].verbose_name, \
             self.weeks_since_anc)
        return string

    def estimated_dd(self):
        return self.encounter.encounter_date + \
            timedelta(30.3475 * (9 - self.pregnancy_month))

    def get_omrs_dict(self):
        igive = {
            'month_of_current_gestation': self.pregnancy_month,
            'antenatal_visit_number': self.anc_visits,
        }
        if self.weeks_since_anc:
            igive.update({'weeks_since_last_anc': self.weeks_since_anc})
        return igive
reversion.register(PregnancyReport, follow=['ccreport_ptr'])


class SPregnancy(PregnancyReport):

    '''SauriPregnancyReport added extra fields specific to Sauri'''
    #shortened the name because of http://code.djangoproject.com/ticket/1820

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_sauri_pregrpt'
        verbose_name = _(u"Sauri Pregnancy Report")
        verbose_name_plural = _(u"Sauri Pregnancy Reports")

    IRON_YES = 'Y'
    IRON_NO = 'N'
    IRON_UNKNOWN = 'U'
    IRON_DOESNOTHAVE = 'X'
    IRON_CHOICES = (
                       (IRON_YES, _('Yes')),
                       (IRON_NO, _('No')),
                       (IRON_UNKNOWN, _('Unkown')),
                       (IRON_DOESNOTHAVE, _('Does not have')))

    FOLIC_YES = 'Y'
    FOLIC_NO = 'N'
    FOLIC_UNKNOWN = 'U'
    FOLIC_DOESNOTHAVE = 'X'
    FOLIC_CHOICES = (
                       (FOLIC_YES, _('Yes')),
                       (FOLIC_NO, _('No')),
                       (FOLIC_UNKNOWN, _('Unkown')),
                       (FOLIC_DOESNOTHAVE, _('Does not have')))

    TESTED_YESREACTIVE = 'YR'
    TESTED_NOREACTIVE = 'NR'
    TESTED_NOUNKNOWN = 'NU'
    TESTED_YESNOTREACTIVE = 'YN'
    TESTED_CHOICES = (
                       (TESTED_YESREACTIVE, _('Yes Reactive')),
                       (TESTED_NOREACTIVE, _('No Reactive')),
                       (TESTED_NOUNKNOWN, _('No Status Unknown')),
                       (TESTED_YESNOTREACTIVE, _('Yes Not Reactive')))

    CD4_YES = 'Y'
    CD4_NO = 'N'
    CD4_UNKNOWN = 'U'
    CD4_CHOICES = (
        (CD4_YES, _(u"Yes")),
        (CD4_NO, _(u"No")),
        (CD4_UNKNOWN, _(u"Unkown")))

    iron_supplement = models.CharField(_(u"Taking Iron supplements"), \
                            max_length=1, choices=IRON_CHOICES, \
                            db_index=True,\
                            help_text=_(u"Is the mother taking iron "\
                                            "supplement?"))

    folic_suppliment = models.CharField(_(u"Taking Folic Acid supplements"), \
                            max_length=1, choices=FOLIC_CHOICES,\
                            db_index=True,\
                            help_text=_(u"Is the mother taking folic acid "\
                                            "supplement?"))

    tested_hiv = models.CharField(_(u"Tested for HIV"), max_length=2, \
                                   choices=TESTED_CHOICES, \
                                   db_index=True,\
                              help_text=_(u"Did the mother get tested for "\
                                            "HIV?"))

    cd4_count = models.CharField(_(u"Completed CD4 Count"), max_length=1, \
                                   choices=CD4_CHOICES, null=True, blank=True,\
                                   db_index=True,\
                                   help_text=_(u"Was CD4 count taken?"))

    pmtc_arv = models.ForeignKey('CodedItem', null=True, blank=True, \
                                    db_index=True,\
                                    verbose_name=_(u"PMTC ARV"))

reversion.register(SPregnancy, follow=['ccreport_ptr'])


class BCPillReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_bcprpt'
        verbose_name = _(u"Birth Control Pill Report")
        verbose_name_plural = _(u"Birth Control Pill Reports")

    pills = models.PositiveSmallIntegerField(_(u"Pills given"), \
                                             null=True, blank=True,\
                                             db_index=True)
    women = models.PositiveSmallIntegerField(_(u"Women given BC pills"),
                                             null=True, blank=True,\
                                             db_index=True)

    def summary(self):
        if self.pills is None:
            pills = _(u"Unkown")
        else:
            pills = unicode(self.pills)
        if self.women is None:
            women = _(u"Unkown")
        else:
            women = unicode(self.women)
        return u"%s: %s, %s: %s" % \
             (self._meta.get_field_by_name('pills')[0].verbose_name, \
              pills, \
              self._meta.get_field_by_name('women')[0].verbose_name, \
              women)

    def get_omrs_dict(self):
        return {'number_of_women_given_bc_pills':
                    self.women}

reversion.register(BCPillReport, follow=['ccreport_ptr'])


class NeonatalReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_neorpt'
        verbose_name = _(u"Neonatal Report")
        verbose_name_plural = _(u"Neonatal Reports")

    clinic_visits = models.PositiveSmallIntegerField(_(u"Clinic Visits"), \
                                    help_text=_(u"Number of clinic visits " \
                                                 "since birth"),\
                                    db_index=True)

    def summary(self):
        return u"%s: %d" % \
             (self._meta.get_field_by_name('clinic_visits')[0].verbose_name, \
              self.clinic_visits)

    def get_omrs_dict(self):
        return {'number_of_health_facility_visits_since_birth':
                    self.clinic_visits}
reversion.register(NeonatalReport, follow=['ccreport_ptr'])


class UnderOneReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_uonerpt'
        verbose_name = _(u"Under One Report")
        verbose_name_plural = _(u"Under One Reports")

    BREAST_YES = 'Y'
    BREAST_NO = 'N'
    BREAST_UNKNOWN = 'U'
    BREAST_CHOICES = (
        (BREAST_YES, _(u"Yes")),
        (BREAST_NO, _(u"No")),
        (BREAST_UNKNOWN, _(u"Unknown")))

    IMMUNIZED_YES = 'Y'
    IMMUNIZED_NO = 'N'
    IMMUNIZED_UNKNOWN = 'U'
    IMMUNIZED_CHOICES = (
        (IMMUNIZED_YES, _(u"Yes")),
        (IMMUNIZED_NO, _(u"No")),
        (IMMUNIZED_UNKNOWN, _(u"Unkown")))

    breast_only = models.CharField(_(u"Breast feeding exclusively"), \
                                   max_length=1, choices=BREAST_CHOICES, \
                                   help_text=_(u"Does the mother " \
                                               "exclusively breast feed?"),\
                                    db_index=True)

    immunized = models.CharField(_(u"Immunized"), max_length=1, \
                                   choices=IMMUNIZED_CHOICES, \
                                   help_text=_(u"Is the child up-to-date on" \
                                                "immunizations?"),\
                                    db_index=True)

    def summary(self):
        return u"%s: %s, %s: %s" % \
            (self._meta.get_field_by_name('breast_only')[0].verbose_name, \
             self.get_breast_only_display(),
             self._meta.get_field_by_name('immunized')[0].verbose_name, \
             self.get_immunized_display())

    def get_omrs_dict(self):

        breast_map = {
            self.BREAST_YES: OpenMRSConsultationForm.YES,
            self.BREAST_NO: OpenMRSConsultationForm.NO,
            self.BREAST_UNKNOWN: OpenMRSConsultationForm.UNKNOWN}

        immun_map = {
            self.IMMUNIZED_YES: OpenMRSConsultationForm.YES,
            self.IMMUNIZED_NO: OpenMRSConsultationForm.NO,
            self.IMMUNIZED_UNKNOWN: OpenMRSConsultationForm.UNKNOWN}

        return {
            'breastfed_exclusively': breast_map[self.breast_only],
            'immunizations_up_to_date': immun_map[self.immunized]}
reversion.register(UnderOneReport, follow=['ccreport_ptr'])


class SUnderOne(UnderOneReport):

    '''Sauri under one report with the extra field for vaccine'''
    #shortened the name because of http://code.djangoproject.com/ticket/1820

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_sauri_uonerpt'
        verbose_name = _(u"Sauri Under One Report")
        verbose_name_plural = _(u"Sauri Under One Reports")

    vaccine = models.ManyToManyField(Vaccine, verbose_name=_(u"Vaccine"))
reversion.register(SUnderOne, follow=['ccreport_ptr'])


class NutritionReport(CCReport):

    '''record nutrition related measurements'''

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_nutrpt'
        verbose_name = _(u"Nutrition Report")
        verbose_name_plural = _(u"Nutrition Reports")

    STATUS_MODERATE = 1
    STATUS_SEVERE = 2
    STATUS_SEVERE_COMP = 3
    STATUS_HEALTHY = 4

    STATUS_CHOICES = (
        (STATUS_MODERATE, _(u"MAM")),
        (STATUS_SEVERE, _(u"SAM")),
        (STATUS_SEVERE_COMP, _(u"SAM+")),
        (STATUS_HEALTHY, _(u"Healthy")))

    OEDEMA_YES = 'Y'
    OEDEMA_NO = 'N'
    OEDEMA_UNKNOWN = 'U'
    OEDEMA_CHOICES = (
        (OEDEMA_YES, _(u"Yes")),
        (OEDEMA_NO, _(u"No")),
        (OEDEMA_UNKNOWN, _(u"Unknown")))

    muac = models.SmallIntegerField(_(u"MUAC (mm)"), blank=True, null=True,\
                                db_index=True)
    oedema = models.CharField(_(u"Oedema"), max_length=1, \
                              choices=OEDEMA_CHOICES,\
                              db_index=True)
    weight = models.FloatField(_(u"Weight (kg)"), blank=True, null=True,\
                            db_index=True)
    status = models.IntegerField(_("Status"),\
                                 choices=STATUS_CHOICES, blank=True, null=True,\
                                db_index=True)

    def diagnose(self):
        '''Diagnosis of the patient'''
        self.status = self.STATUS_HEALTHY
        if self.muac is None or self.muac == 0:
            self.status = None
        elif self.oedema == 'Y' or self.muac < 110:
            self.status = self.STATUS_SEVERE
        elif self.muac < 125:
            self.status = self.STATUS_MODERATE
        print (self.muac, self.oedema, self.status)

    def save(self, *args):
        if self.status is None:
            self.diagnose()
        super(NutritionReport, self).save(*args)

    def summary(self):
        strings = []
        if self.muac:
            strings.append(u"%s: %s" %
                    (self._meta.get_field_by_name('muac')[0].verbose_name, \
                     self.muac))
        strings.append(u"%s: %s" %
                (self._meta.get_field_by_name('oedema')[0].verbose_name, \
                 self.get_oedema_display()))
        if self.weight:
            strings.append(u"%s: %s" %
                    (self._meta.get_field_by_name('weight')[0].verbose_name, \
                     self.weight))
        if self.status:
            strings.append(u"%s: %s" %
                    (self._meta.get_field_by_name('status')[0].verbose_name, \
                     self.get_status_display()))
        return u", ".join(strings)

    @property
    def verbose_state(self):
        for k, v in self.STATUS_CHOICES:
            if self.status == k:
                return v

    def get_omrs_dict(self):

        oedema_map = {
            self.OEDEMA_YES: OpenMRSConsultationForm.YES,
            self.OEDEMA_NO: OpenMRSConsultationForm.NO,
            self.OEDEMA_UNKNOWN: OpenMRSConsultationForm.UNKNOWN,
        }

        igive = {
            'mid_upper_arm_circumference': self.muac,
            'oedema': oedema_map[self.oedema]}
        if self.weight:
            igive.update({'weight': self.weight})
        if self.oedema == self.OEDEMA_YES:
            igive.update({'reasons_for_referral__oedema': True})
        return igive
reversion.register(NutritionReport, follow=['ccreport_ptr'])


class FeverReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_fevrpt'
        verbose_name = _(u"Fever Report")
        verbose_name_plural = _(u"Fever Reports")

    RDT_POSITIVE = 'P'
    RDT_NEGATIVE = 'N'
    RDT_UNKNOWN = 'U'

    RDT_CHOICES = (
        (RDT_POSITIVE, _(u"Positive")),
        (RDT_NEGATIVE, _(u"Negative")),
        (RDT_UNKNOWN, _(u"Unknown")))

    rdt_result = models.CharField(_(u"RDT Result"), max_length=1, \
                                  choices=RDT_CHOICES,\
                                  db_index=True)

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('rdt_result')[0].verbose_name, \
             self.get_rdt_result_display())

    def get_omrs_dict(self):

        rdt_map = {
            self.RDT_POSITIVE: OpenMRSConsultationForm.POSITIVE,
            self.RDT_NEGATIVE: OpenMRSConsultationForm.NEGATIVE,
            # HERE. mapped UNKNOWN as INDETERMINATE
            self.RDT_UNKNOWN: OpenMRSConsultationForm.INDETERMINATE,
        }

        return {
            'rapid_test_for_malaria': rdt_map[self.rdt_result]}
reversion.register(FeverReport, follow=['ccreport_ptr'])


class MedicineGivenReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_medsrpt'
        verbose_name = _(u"Medicine Given Report")
        verbose_name_plural = _(u"Medicine Given Reports")

    medicines = models.ManyToManyField('CodedItem', \
                                         verbose_name=_(u"Medicines"))

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('medicines')[0].verbose_name, \
             u", ".join([ds.description for ds in self.medicines.all()]))

    def short_summary(self):
        return u", ".join([ds.description for ds in self.medicines.all()])
    def get_omrs_dict(self):
        igive = {}
        value = []
        for med in self.medicines.all():
            if med.code.upper() == 'ACT':
                value.append(OpenMRSConsultationForm.MEDIC_ORDER_ANTIMALARIAL)
            if med.code.upper() == 'R':
                value.append(OpenMRSConsultationForm.MEDIC_ORDER_ORS)
            if med.code.upper() == 'Z':
                value.append(OpenMRSConsultationForm.MEDIC_ORDER_ZINC)
        if len(value):
            igive.update({'current_medication_order': value})
        return igive
reversion.register(MedicineGivenReport, follow=['ccreport_ptr'])


class ReferralReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_refrpt'
        verbose_name = _(u"Referral Report")
        verbose_name_plural = _(u"Referral Reports")

    URGENCY_AMBULANCE = 'A'
    URGENCY_EMERGENCY = 'E'
    URGENCY_BASIC = 'B'
    URGENCY_CONVENIENT = 'C'
    URGENCY_CHOICES = (
                       (URGENCY_AMBULANCE, _('Ambulance Referral')),
                       (URGENCY_EMERGENCY, _('Emergency Referral')),
                       (URGENCY_BASIC, _('Basic Referral')),
                       (URGENCY_CONVENIENT, _('Convenient Referral')))

    urgency = models.CharField(_(u"Urgency"), max_length=1, \
                               choices=URGENCY_CHOICES,\
                               db_index=True)

    @property
    def verbose_urgency(self):
        for k, v in self.URGENCY_CHOICES:
            if self.urgency == k:
                return v

    def summary(self):
        return u"%s: %s" % \
            (self._meta.get_field_by_name('urgency')[0].verbose_name, \
             self.get_urgency_display())

    def get_omrs_dict(self):

        prio_map = {
            self.URGENCY_AMBULANCE: OpenMRSConsultationForm.REFERRAL_AMBULANCE,
            self.URGENCY_EMERGENCY: OpenMRSConsultationForm.REFERRAL_EMERGENCY,
            # HERE. mapped BASIC as URGENT.
            self.URGENCY_BASIC: OpenMRSConsultationForm.REFERRAL_URGENT,
            self.URGENCY_CONVENIENT: \
                              OpenMRSConsultationForm.REFERRAL_WHEN_CONVENIENT,
        }
        return {'referral_priority': prio_map[self.urgency]}
reversion.register(ReferralReport, follow=['ccreport_ptr'])


class HouseholdVisitReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_hhvisitrpt'
        verbose_name = _(u"Household Visit Report")
        verbose_name_plural = _(u"Household Visit Reports")

    available = models.BooleanField(_(u"HH Member Available"), \
                                help_text=_(u"Was a houshold member " \
                                             "available?"),\
                                db_index=True)

    children = models.SmallIntegerField(_("Children Under Five"), \
                                        blank=True, null=True, \
                            help_text=_("Number of children under 5 seen"),\
                            db_index=True)

    counseling = models.ManyToManyField('CodedItem', \
                       verbose_name=_(u"Counseling / advice topics covered"), \
                       blank=True)

    def summary(self):
        string = u"%s: %s" % \
                (self._meta.get_field_by_name('available')[0].verbose_name, \
                 bool(self.available))
        if self.available and self.children is not None:
            string += ", %s: %d" % \
                (self._meta.get_field_by_name('children')[0].verbose_name, \
                 self.children)
        return string

    def get_omrs_dict(self):
        if self.available:
            avail = OpenMRSHouseholdForm.YES
        else:
            avail = OpenMRSHouseholdForm.NO
        igive = {
            'hh_member_available': avail,
        }
        if self.children != None:
            igive.update({'number_children_under_five': self.children})
        for ct in self.counseling.all():
            if ct.code.upper() == 'NUT':
                igive.update({'counseling_topics__nutrition': True})
            elif ct.code.upper() in ('FP', 'BP'):
                igive.update({'counseling_topics__family_planning': True})
            elif ct.code.upper() == 'SH':
                igive.update({'counseling_topics__sanitation_and_hygiene': \
                            True})
            elif ct.code.upper() == 'BF':
                igive.update({'counseling_topics__breastfeeding': True})
            elif ct.code.upper() == 'BN':
                igive.update({'counseling_topics__bednet': True})
            elif ct.code.upper() == 'IM':
                igive.update({'counseling_topics__immunizations': True})
            else:
                igive.update({'counseling_topics__other_non_coded': True})
        return igive
reversion.register(HouseholdVisitReport, follow=['ccreport_ptr'])


class FamilyPlanningReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_fprpt'
        verbose_name = _(u"Family Planning Report")
        verbose_name_plural = _(u"Family Planning Reports")

    women = models.PositiveSmallIntegerField(_(u"Women"), \
                            help_text=_(u"Number of women aged 15 to 49 " \
                                         "seen during visit"),\
                            db_index=True)

    women_using = models.PositiveSmallIntegerField(_(u"Women using FP"), \
                                                null=True, blank=True, \
                                                db_index=True,\
                            help_text=_(u"Number of the women using " \
                                         "modern family planning"))

    def summary(self):
        string = u"%s: %d" % \
                    (self._meta.get_field_by_name('women')[0].verbose_name, \
                     self.women)
        if self.women_using is not None:
            string += ", %s: %d" % (self._meta.get_field_by_name(\
                                            'women_using')[0].verbose_name, \
                                   self.women_using)
            if self.familyplanningusage_set.all().count() > 0:
                string += " (%s)" % \
                            ", ".join([unicode(fpu) for fpu in \
                                        self.familyplanningusage_set.all()])
        return string

    def get_omrs_dict(self):
        return {
            'women_seen': self.women,
            'women_using_family_planning': self.women_using,
        }
reversion.register(FamilyPlanningReport, \
                   follow=['ccreport_ptr', 'familyplanningusage_set'])


class SickMembersReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_sickrpt'
        verbose_name = _(u"Sick Household Members Report")
        verbose_name_plural = _(u"Sick Household Members Reports")

    sick = models.PositiveSmallIntegerField(_(u"Others sick"), \
                           help_text=_(u"Number of other sick household " \
                                        "members seen during visit"),\
                            db_index=True)

    rdts = models.PositiveSmallIntegerField(_(u"RDTs"), \
                           help_text=_(u"Number of RDTs used on other " \
                                        "sick household members"),\
                            db_index=True)

    positive_rdts = models.PositiveSmallIntegerField(_(u"Positive RDTs"), \
                           help_text=_(u"Number of positve RDTs cases for " \
                                        "other sick household members"),\
                            db_index=True)

    on_treatment = models.PositiveSmallIntegerField(_(u"Others on treatment"),\
                           help_text=_(u"Number of other sick household " \
                                        "members receiving anti-malarial " \
                                        "treatment"),\
                            db_index=True)

    def summary(self):
        return u"%s: %d, %s: %d, %s: %d, %s: %d" % \
            (self._meta.get_field_by_name('sick')[0].verbose_name, \
             self.sick,
             self._meta.get_field_by_name('rdts')[0].verbose_name, \
             self.rdts,
             self._meta.get_field_by_name('positive_rdts')[0].verbose_name, \
             self.positive_rdts,
             self._meta.get_field_by_name('on_treatment')[0].verbose_name, \
             self.on_treatment)

    def get_omrs_dict(self):
        return {
            'other_sick_members': self.sick,
            'rdts_used': self.rdts,
            'positive_rdts': self.positive_rdts,
            'other_sick_members_on_treatment': self.on_treatment,
        }
reversion.register(SickMembersReport, follow=['ccreport_ptr'])


class VerbalAutopsyReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_autopsyrpt'
        verbose_name = _(u"Verbal Autopsy Report")
        verbose_name_plural = _(u"Verbal Autopsy Reports")

    done = models.BooleanField(_("Completed?"), \
                                help_text=_('Was a Verbal Autopsy conducted?'),\
                                db_index=True)


class BedNetReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_bnrpt'
        verbose_name = _(u"Bednet Report")
        verbose_name_plural = _(u"Bednet Reports")

    sleeping_sites = models.PositiveSmallIntegerField(_(u"Sleeping sites"),\
                            help_text=_(u"Number of sleeping sites"),\
                            db_index=True)

    function_nets = models.PositiveSmallIntegerField(_(u"Recent Bednets"), \
                            help_text=_(u"Number of functioning bednets"),\
                            db_index=True)
    earlier_nets = models.PositiveSmallIntegerField(_(u"Earlier Bednets"), \
                            help_text=_(u"Number of bednets received" \
                            " earlier "),\
                            db_index=True)
    damaged_nets = models.PositiveSmallIntegerField(_(u"Damaged Bednets"), \
                            help_text=_(u"Number of recent bednets that are" \
                                        " damaged"),\
                            db_index=True)

    def summary(self):
        return u"%s: %d, %s: %d" % \
            (self._meta.get_field_by_name('sleeping_sites')[0].verbose_name, \
             self.sleeping_sites, \
             self._meta.get_field_by_name('function_nets')[0].verbose_name, \
             self.nets)

reversion.register(BedNetReport, follow=['ccreport_ptr'])

class ExtendedBedNetReport(BedNetReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_ebnrpt'
        verbose_name = _(u"Extended Bednet Report")
        verbose_name_plural = _(u"Extended Bednet Reports")

    people = models.PositiveSmallIntegerField(_(u"Number of people"), \
                            help_text=_(u"Number of people who are " \
                                        "sleeping in the household"),\
                            db_index=True)

reversion.register(ExtendedBedNetReport, follow=['ccreport_ptr'])

class BednetUtilization(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_bdnutil_rpt'
        verbose_name = _(u"Bednet utilization Report")
        verbose_name_plural = _(u"Bednet utilization reports")

    DONT_HAVE = 'NH'
    BEDNET_DAMAGED = 'BD'
    DIFFICULT_HUNG = 'DH'
    SMALL_ROOM = 'SR'
    DIFFICULT_BREATHE = 'DB'
    NOT_EFFECTIVE = 'NE'
    OTHER = 'Z'
    UNKNOWN = 'U'
    U = -1

    REASON_CHOICES = (
        (DIFFICULT_BREATHE, _(u'Difficulty to breathe')),
        (NOT_EFFECTIVE, _(u'Doubt about effectiveness')),
        (SMALL_ROOM, _(u'Room too small')),
        (DIFFICULT_HUNG, _(u'Difficulty to hang')),
        (BEDNET_DAMAGED, _(u'Bednet damaged')),
        (DONT_HAVE, _(u'No bednet')),
        (UNKNOWN, _(u'Unknown')),
        (OTHER, _(u'Other')))

    child_underfive = models.PositiveSmallIntegerField(_(u"children under" \
                            " five "), help_text=_(u"Number of children " \
                            "under five who slept here last night."),\
                            db_index=True)
    child_lastnite = models.PositiveSmallIntegerField(_(u"Children slept " \
                            "under bednet"), \
                            db_index=True,\
                            help_text=_(u"Number of children" \
                            " under five who slept under bednet last night."))
    hanging_bednet = models.SmallIntegerField(_(u"Number of hanging bednet"), \
                            db_index=True,\
                            help_text=_(u"Number of hanging bednet"))
    reason = models.CharField(_(u"Reason "), \
                            help_text=_(u"reason why some children didn't" \
                            " sleep under bednet"), null=True, blank=True, \
                            db_index=True, \
                            max_length=2, choices=REASON_CHOICES)

    def summary(self):
        return u"%s: %d, %s: %d" % \
            (self._meta.get_field_by_name('child_underfive')[0].verbose_name, \
             self.child_underfive, \
             self._meta.get_field_by_name('child_lastnite')[0].verbose_name, \
             self.child_lastnite)

reversion.register(BednetUtilization, follow=['ccreport_ptr'])


class SanitationReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_sanitation_rpt'
        verbose_name = _(u"Sanitation Report")
        verbose_name_plural = _(u"Sanitation Reports")

    FLUSH = 'FL'
    VENTILATED_IMPROVED_PIT = 'VP'
    PITLAT_WITH_SLAB = 'PY'
    PITLAT_WITHOUT_SLAB = 'PN'
    COMPOSTING_TOILET = 'CT'
    BUCKET = 'BT'
    HANGING_TOILET_LAT = 'HT'
    NO_FACILITY_OR_BUSH = 'NS'
    OTHER = 'Z'

    TOILET_LAT_CHOICES = (
        (FLUSH, _(u'Flush')),
        (VENTILATED_IMPROVED_PIT, _(u'Ventilated Improved Pit Latrine')),
        (PITLAT_WITH_SLAB, _(u'Pit Latrine with slab')),
        (PITLAT_WITHOUT_SLAB, _(u'Pit Latrine without slab')),
        (COMPOSTING_TOILET, _(u'Compositing Pit Toilet')),
        (BUCKET, _(u'Bucket')),
        (HANGING_TOILET_LAT, _(u'Hanging Toilet Latrine')),
        (NO_FACILITY_OR_BUSH, _(u'No facility')),
        (OTHER, _(u'Other')))

    PB = -2
    U = -1

    toilet_lat = models.CharField(_(u"Toilet Type"), max_length=2, \
                              choices=TOILET_LAT_CHOICES,\
                              db_index=True)
    share_toilet = models.SmallIntegerField(_(u"How many shares?"), \
                                help_text=_(u"How many people" \
                                " share the toilet (open to public = -1, " \
                                "unknown = -2 )"),\
                                db_index=True)
reversion.register(SanitationReport, follow=['ccreport_ptr'])


class DrinkingWaterReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_drnkwater_rpt'
        verbose_name = _(u"Drinking Water Report")
        verbose_name_plural = _(u"Drinking Water Reports")

    PIPED_WATER = 'PP'
    PUBLIC_TAP_STANDPIPE = 'PT'
    TUBEWELL_BOREHOLE = 'TB'
    PROTECTED_DUG_WELL = 'PW'
    UNPROTECTED_DUG_WELL = 'UW'
    PROTECTED_SPRING = 'PS'
    UNPROTECTED_SPRING = 'UP'
    RAIN_COLLECTION = 'RW'
    SURFACE_WATER = 'SU'
    OTHER = 'Z'

    DRNKWATER_CHOICES = (
        (PIPED_WATER, _(u'Piped water into dwelling or yard/plot')),
        (PUBLIC_TAP_STANDPIPE, _(u'Public Tap/Standpipe')),
        (TUBEWELL_BOREHOLE, _(u'Tube well / Borehole')),
        (PROTECTED_DUG_WELL, _(u'Protected dug well')),
        (UNPROTECTED_DUG_WELL, _(u'Unprotected Dug well')),
        (PROTECTED_SPRING, _(u'Protected Spring')),
        (UNPROTECTED_SPRING, _(u'Unprotected spring')),
        (RAIN_COLLECTION, _(u'Rain water collection')),
        (SURFACE_WATER, _(u'Surface water (river, dam, lake, pond, stream')),
        (OTHER, _(u'Other')))

    TREATMENT_METHOD_BOIL = 'BW'
    TREATMENT_METHOD_DONATED_CHLORINE = 'DC'
    TREATMENT_METHOD_BOUGHT_CHLORINE = 'BC'
    TREATMENT_METHOD_CLOTH = 'SC'
    TREATMENT_METHOD_WATERFILTER = 'WF'
    TREATMENT_METHOD_SOLARDISINFECTION = 'SR'
    TREATMENT_METHOD_STAND_SETTLE = 'LS'
    TREATMENT_METHOD_OTHER = 'Z'
    TREATMENT_METHOD_DONTKNOW = 'U'
    TREATMENT_CHOICES = (
        (TREATMENT_METHOD_BOIL, _(u"Boil water")),
        (TREATMENT_METHOD_DONATED_CHLORINE, _(u"Donated bleach/chlorine")),
        (TREATMENT_METHOD_BOUGHT_CHLORINE, _(u"Bought bleach/chlorine")),
        (TREATMENT_METHOD_CLOTH, _(u"Strain it through cloth")),
        (TREATMENT_METHOD_WATERFILTER, _(u"Use water filter: sand/ceramic")),
        (TREATMENT_METHOD_SOLARDISINFECTION, _(u"Solar disinfection")),
        (TREATMENT_METHOD_STAND_SETTLE, _(u"Let it stand and settle")),
        (TREATMENT_METHOD_OTHER, _(u"Other")),
        (TREATMENT_METHOD_DONTKNOW, _(u"Unknown")),)

    water_source = models.CharField(_(u"Water Source"), max_length=2, \
                              choices=DRNKWATER_CHOICES,\
                              db_index=True)
    treatment_method = models.CharField(_(u"Treatment method"), max_length=2, \
                              choices=TREATMENT_CHOICES, help_text=_(u"What " \
                                "do you use to make it safer to drink"), \
                                blank=True, db_index=True)
reversion.register(DrinkingWaterReport, follow=['ccreport_ptr'])


class BednetIssuedReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_bdnstc_rpt'
        verbose_name = _(u"Bednet Distribution Report")
        verbose_name_plural = _(u"Betnet Distribution Reports")

    bednet_received = models.PositiveSmallIntegerField(_(u"Bed net received"),\
                            db_index=True)

reversion.register(BednetIssuedReport, follow=['ccreport_ptr'])


class AntenatalVisitReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_iavrpt'
        verbose_name = _(u"Initial Antenatal Visit Report")
        verbose_name_plural = _(u"Initial Antenatal Visit Reports")

    expected_on = models.DateTimeField(_(u"Expected Date of Delivery"),\
                        db_index=True)
    sms_alert = models.ForeignKey(SmsAlertModel, null=True, blank=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('expected_on')[0].verbose_name, \
             self.expected_on)
        return string
reversion.register(AntenatalVisitReport, follow=['ccreport_ptr'])


class AppointmentReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_appointment'
        verbose_name = _(u"Appointment")
        verbose_name_plural = _(u"Appointments")

    STATUS_OPEN = 0
    STATUS_CLOSED = 2
    STATUS_PENDING_CV = 1

    STATUS_CHOICES = (
        (STATUS_OPEN, _(u"Open")),
        (STATUS_CLOSED, _(u"Closed")),
        (STATUS_PENDING_CV, _(u"Pending Clinic Visit")))

    appointment_date = models.DateTimeField(_(u"Next appointment"), \
                                            db_index=True)
    closed_date = models.DateTimeField(_(u"Date closed"), blank=True, \
                                        null=True, db_index=True)
    status = models.PositiveSmallIntegerField(_("Status"), \
                                                choices=STATUS_CHOICES,
                                db_index=True,\
                                help_text=_(u"Is the appointment still open" \
                                            " or closed?"), \
                                            default=STATUS_OPEN)
    task_id = models.CharField('Task ID', max_length=255, \
                                            db_index=True, \
                                            null=True, blank=True)
    sms_alert = models.ForeignKey(SmsAlertModel, null=True, blank=True,
                                            db_index=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('appointment_date')[0].verbose_name,\
             self.appointment_date)
        return string

    def get_omrs_dict(self):
        '''OpenMRS Key/Value dict.

        Return key/value dictionary of openmrs values that this report can
        populate
        '''
        return {'return_visit_date': self.appointment_date}
reversion.register(AppointmentReport, follow=['ccreport_ptr'])


class PregnancyRegistrationReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_pregregrpt'
        verbose_name = _(u"Pregnancy Registration")
        verbose_name_plural = _(u"Pregnancy Registrations")

    MARRIED_YES = 'Y'
    MARRIED_NO = 'N'
    MARRIED_UNKNOWN = 'U'
    MARRIED_CHOICES = (
        (MARRIED_YES, _(u"Yes")),
        (MARRIED_NO, _(u"No")),
        (MARRIED_UNKNOWN, _(u"Unknown")))

    married = models.CharField(_(u"Married?"), max_length=1, \
                                        choices=MARRIED_CHOICES,\
                                        db_index=True)
    pregnancies = models.PositiveSmallIntegerField(_("Number of Pregancies"),\
                                        db_index=True)
    number_of_children = models.PositiveSmallIntegerField(_("Number of " \
                                                            "Pregancies"), \
                                                            default=0,\
                                                            db_index=True,\
                                                        blank=True, null=True)
    husband = models.ForeignKey('Patient', blank=True, null=True, \
                                    db_index=True,\
                                  verbose_name=_(u"Husband"), \
                                  help_text=_(u"The husband to this pregnant"\
                                            " woman"),\
                                  related_name='husband')

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('married')[0].verbose_name, \
            self.married)
        string += u", %s: %s" % \
            (self._meta.get_field_by_name('pregnancies')[0].verbose_name, \
            self.pregnancies)
        string += u", %s: %s" % \
            (self._meta.get_field_by_name('number_of_children')[0]\
                .verbose_name, self.number_of_children)
        return string

    def get_omrs_dict(self):
        '''OpenMRS Key/Value dict.

        Return key/value dictionary of openmrs values that this report can
        populate
        '''
        return {'total_offspring_living_in_home': self.number_of_children}
reversion.register(PregnancyRegistrationReport, follow=['ccreport_ptr'])


class HIVTestReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_hivtest'
        verbose_name = _(u"HIV Test")
        verbose_name_plural = _(u"HIV Tests")

    HIV_YES = 'Y'
    HIV_NO = 'N'
    HIV_UNKNOWN = 'U'
    HIV_NOCONSENT = 'NC'
    HIV_CHOICES = (
        (HIV_YES, _(u"Yes")),
        (HIV_NO, _(u"No")),
        (HIV_UNKNOWN, _(u"Unknown")),
        (HIV_NOCONSENT, _(u"No Consent")))
    BLOOD_DRAWN_YES = 'Y'
    BLOOD_DRAWN_NO = 'N'
    BLOOD_DRAWN_UNKNOWN = 'U'
    BLOOD_DRAWN_CHOICES = (
        (BLOOD_DRAWN_YES, _(u"Yes")),
        (BLOOD_DRAWN_NO, _(u"No")),
        (BLOOD_DRAWN_UNKNOWN, _(u"Unknown")))

    hiv = models.CharField(_(u"HIV+?"), max_length=2, \
                              choices=HIV_CHOICES, db_index=True)
    blood_drawn = models.CharField(_(u"Blood drawn?"), max_length=1, \
                                        choices=BLOOD_DRAWN_CHOICES,\
                                        db_index=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('hiv')[0].verbose_name, \
            self.hiv)
        string += u", %s: %s" % \
            (self._meta.get_field_by_name('blood_drawn')[0].verbose_name, \
            self.blood_drawn)
        return string

    def get_omrs_dict(self):
        '''OpenMRS Key/Value dict.

        Return key/value dictionary of openmrs values that this report can
        populate
        '''
        info = {'blood_drawn_for_cd4_count': self.blood_drawn}
        if self.hiv ==self.HIV_YES:
            info.update({'hiv_test': True})
        if self.hiv == self.HIV_NO:
            info.update({'hiv_test': False})
        return info
reversion.register(HIVTestReport, follow=['ccreport_ptr'])


class DBSResultReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_dbsresult'
        verbose_name = _(u"DBS Result")
        verbose_name_plural = _(u"DBS Results")

    RESULT_POSITIVE = True
    RESULT_NEGATIVE = False
    RESULT_CHOICES = (
        (RESULT_POSITIVE, _(u"Yes")),
        (RESULT_NEGATIVE, _(u"No")))
    test_result = models.BooleanField(_(u"Test Result"), \
                                        choices=RESULT_CHOICES,
                                        db_index=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('test_result')[0].verbose_name, \
            self.test_result)
        return string

    def get_omrs_dict(self):
        '''OpenMRS Key/Value dict.

        Return key/value dictionary of openmrs values that this report can
        populate
        '''
        return {'hiv_infected': self.test_result}
reversion.register(DBSResultReport, follow=['ccreport_ptr'])


class CD4ResultReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_cd4result'
        verbose_name = _(u"CD4 Result")
        verbose_name_plural = _(u"CD4 Results")

    cd4_count = models.PositiveIntegerField(_(u"CD4 Count"), db_index=True)

    def summary(self):
        string = u"%s: %s" % \
            (self._meta.get_field_by_name('cd4_count')[0].verbose_name, \
            self.cd4_count)
        return string
reversion.register(CD4ResultReport, follow=['ccreport_ptr'])


class PatientStatusReport(CCReport):

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_patientstatus'
        verbose_name = _(u"Patient status Report")
        verbose_name_plural = _(u"Patients status Report")

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _(u"Alive")),
        (STATUS_INACTIVE, _(u"Relocated")))

    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES,\
                                    db_index=True)
    reason = models.CharField(_(u"Reason"), max_length=100, blank=True,
                                null=True, db_index=True)

reversion.register(PatientStatusReport, follow=['ccreport_ptr'])
