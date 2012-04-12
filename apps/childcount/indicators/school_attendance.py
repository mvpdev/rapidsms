'''
Sanitation Report
'''

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import SchoolAttendanceReport

NAME = _("School Attendance")


class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
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
