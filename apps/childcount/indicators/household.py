'''
Household Visit Report
'''
from datetime import timedelta

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorDifference
from indicator import IndicatorPercentage
from indicator import Percentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import HouseholdVisitReport

from childcount.indicators import registration

NAME = _("Household")


class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("HH Visits")
    long_name   = _("Total number of household visits")

    @classmethod
    def _value(cls, period, data_in):
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .count()

class Unique(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique"
    short_name  = _("Uniq. HH Visits")
    long_name   = _("Total number of visits to unique households")

    @classmethod
    def _value(cls, period, data_in):
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class UniqueNinetyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique_ninety_days"
    short_name  = _("Uniq. HHV 90d")
    long_name   = _("Total number of visits to unique households "\
                    "in the 90 days ending at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(90))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UniqueThirtyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique_thirty_days"
    short_name  = _("Uniq. HHV 30d")
    long_name   = _("Total number of visits to unique households "\
                    "in the 30 days ending at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(30))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class CoveragePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    type_out    = Percentage

    slug        = "coverage_perc"
    short_name  = _("% HH Coverage (90 days)")
    long_name   = _("Percentage of households getting "\
                    "a visit in the last 90 days as of "\
                    "the end of this time period")

    cls_num     = UniqueNinetyDays
    cls_den     = registration.Household


class CoveragePerc30(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    type_out    = Percentage

    slug        = "coverage_perc30"
    short_name  = _("% HH Coverage (30 days)")
    long_name   = _("Percentage of households getting "\
                    "a visit in the last 30 days as of "\
                    "the end of this time period")

    cls_num     = UniqueThirtyDays
    cls_den     = registration.Household


class OnTime(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "on_time"
    short_name  = _("On-Time HH Visits")
    long_name   = _("Number of unique households getting "\
                    "a visit in the last 90 days and also in the 90 "\
                    "days before their last visit.")

    @classmethod
    def _value(cls, period, data_in):
        if data_in.count() == 0:
            return 0

        pks = ','.join([str(patient.pk) for patient in data_in])
        date_end   = period.end.strftime('%Y-%m-%d %H:%M:%S')
       
        cursor = connection.cursor()
        q='''
        /* Get the total number of rows */
        SELECT 
            COUNT(*)
        FROM
            /* This SELECT has one row for every household we want to count...
                That is, it's one row for every household that has been visited
                on time. */
            (SELECT
                `latest_visits`.`patient_id`,
                `latest_visits`.`cur_date`
                /* MIN(DATEDIFF(`latest_visits`.`cur_date`, `cc_encounter2`.`encounter_date`))*/

            FROM
                /* This sub-query gets the latest household visit for each household */
                (SELECT
                    `cc_patient`.`id` AS `patient_id`,
                    `cc_patient`.`created_on` AS `created_on`,
                    GREATEST(`cc_patient`.`created_on`, MAX(`cc_encounter`.`encounter_date`)) AS `cur_date`

                FROM `cc_patient`

                LEFT JOIN `cc_encounter`
                    ON (`cc_patient`.`id`=`cc_encounter`.`patient_id`   
                        AND `cc_encounter`.`encounter_date` <= "%(date_end)s")
                LEFT JOIN `cc_ccrpt`
                    ON (`cc_encounter`.`id`=`cc_ccrpt`.`encounter_id`)
                INNER JOIN `cc_hhvisitrpt`
                    ON (`cc_ccrpt`.`id`=`cc_hhvisitrpt`.`ccreport_ptr_id`)

                GROUP BY `cc_patient`.`id`) AS `latest_visits`

            LEFT JOIN `cc_encounter`      AS `cc_encounter2`
                ON (`latest_visits`.`patient_id`=`cc_encounter2`.`patient_id` 
                    AND `latest_visits`.`cur_date` > `cc_encounter2`.`encounter_date`)
            LEFT JOIN `cc_ccrpt`          AS `cc_ccrpt2` 
                ON (`cc_encounter2`.`id`=`cc_ccrpt2`.`encounter_id`)
            INNER JOIN `cc_hhvisitrpt`    AS `cc_hhvisitrpt2` 
                ON (`cc_ccrpt2`.`id`=`cc_hhvisitrpt2`.`ccreport_ptr_id`)

            WHERE

                /* The difference between the latest visit and the second-latest visit should
                    be between 0 and 90 days... If there's no second-latest visit, we consider
                    the registration date instead. */
                DATEDIFF(`latest_visits`.`cur_date`, 
                    GREATEST(`latest_visits`.`created_on`, `cc_encounter2`.`encounter_date`)) < 90 AND
                DATEDIFF(`latest_visits`.`cur_date`, 
                    GREATEST(`latest_visits`.`created_on`, `cc_encounter2`.`encounter_date`)) > 0 AND
                `latest_visits`.`patient_id` IN (%(patient_pks)s) AND
                /* We only care about visits before END */
                `latest_visits`.`cur_date` <= "%(date_end)s" AND
                /* We require the most recent visit to be within the 90 days of END */
                `latest_visits`.`cur_date` > DATE_SUB("%(date_end)s", INTERVAL 90 DAY)

            GROUP BY `patient_id`) as `unique_otv`
        ''' % {'patient_pks' : pks, 
                'date_end': date_end}

        cursor.execute(q)
        return int(cursor.fetchone()[0])

class Late(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "late"
    short_name  = _("Late HH Visits")
    long_name   = _("Total number of late visits to unique households")

    cls_first   = Total
    cls_second  = OnTime

class OnTimePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    type_out    = Percentage

    slug        = "on_time_perc"
    short_name  = _("% On-Time HH Visits")
    long_name   = _("Percentage of households getting an on-time visit")

    cls_num     = OnTime
    cls_den     = registration.Household


class HasUnderFive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "hasunderfive"
    short_name  = _("Underfive")
    long_name   = _("Total Unique Visits for last 30 days")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .alive(period.start, period.end)\
            .under_five(period.start, period.end)\
            .value('household')\
            .distinct()

        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__health_id__in=households,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(30))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class UnderFiveUnique_visit(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "hasunderfive"
    short_name  = _("Unique Household Visit #UnderFive")
    long_name   = _("Unique Household Visits with UnderFive for last 30 days")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .created_before(period.end)\
            .alive(period.start, period.end)\
            .under_five(period.start, period.end)\
            .values('household')\
            .distinct()

        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__health_id__in=households,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(30))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class HasPregnancy(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "haspregnancy"
    short_name  = _("Unique Household Visit #Pregnancy")
    long_name   = _("Unique Household visit with Pregnancy for last 30 days")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .created_before(period.end)\
            .alive(period.start, period.end)\
            .pregnant(period.start, period.end)\
            .values('household')\
            .distinct()

        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__health_id__in=households,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(30))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class HasNeonatal(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "hasneonatal"
    short_name  = _("Unique Household Visit #Neonatal")
    long_name   = _("Unique Household visit with Neonatal for last 7 days")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .created_before(period.end)\
            .alive(period.start, period.end)\
            .neonatal(period.start, period.end)\
            .values('household')\
            .distinct()

        return HouseholdVisitReport\
            .objects\
            .filter(encounter__patient__health_id__in=households,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(7))\
            .values('encounter__patient')\
            .distinct()\
            .count()
