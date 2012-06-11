'''
School Attendance
'''

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator

from django.db.models import F, Q
from django.db.models.aggregates import Sum
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import SchoolAttendanceReport

NAME = _("School Attendance")


class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# School Attendance reports")
    long_name   = _("Total number of School Attendance reports "\
                    "for unique households during this period")

    @classmethod
    def _value(cls, period, data_in):
        return SchoolAttendanceReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class PrimarySchoolAged(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "primaryschoolaged"
    short_name  = _("# SchoolAgedKids")
    long_name   = _("Total number of school aged children in a particular " \
                    "household")

    @classmethod
    def _value(cls, period, data_in):
        return SchoolAttendanceReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .exclude(household_pupil=-1)\
            .distinct()\
            .aggregate(total=Sum('household_pupil'))['total'] or 0


class PrimarySchoolAttending(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "primaryschoolattending"
    short_name  = _("# pupils")
    long_name   = _("Total number of children currently attending school " \
                    "at last visit for unique households during time period")

    @classmethod
    def _value(cls, period, data_in):
        return SchoolAttendanceReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .distinct()\
            .aggregate(total=Sum('attending_school'))['total'] or 0


class NumberOfHouseholdsWithRecordedSchoolNotInSession(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "totalnotinsession"
    short_name  = _("# Households School NOT in Session")
    long_name   = _("Number of unique households with a recorded SA1=\"N\""
                    " [School NOT in Session] during time period")

    @classmethod
    def _value(cls, period, data_in):
        return SchoolAttendanceReport\
            .objects\
            .filter(encounter__patient__in=data_in, household_pupil=-1, \
                encounter__encounter_date__range=(period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UniqueOneEightyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int
    total_column = False
    
    slug        = "unique_oneeighty_days"
    short_name  = _("Uniq. Household reports for 180d")
    long_name   = _("Total number of School attendance to unique households "\
                    "in the 180 days ending at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return SchoolAttendanceReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(180))\
            .values('encounter__patient')\
            .distinct()\
            .count()
