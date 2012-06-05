'''
Sanitation Report
'''

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import SanitationReport

NAME = _("Sanitation")

improved = [SanitationReport.FLUSH,
            SanitationReport.PITLAT_WITH_SLAB,
            SanitationReport.VENTILATED_IMPROVED_PIT,
            SanitationReport.COMPOSTING_TOILET]

share = SanitationReport.SHARE_NO


class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Total number of sanitation reports")

    @classmethod
    def _value(cls, period, data_in):
        return SanitationReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .count()

class UniqueHousehold(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "uniqueSANReports"
    short_name  = _("#Unique +SAN Reports")
    long_name   = _("Total number of Unique sanitation reports")

    @classmethod
    def _value(cls, period, data_in):
        return SanitationReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class UsingImprovedSanitation(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "improvedSanitation"
    short_name  = _("#Using Improved Sanitation")
    long_name   = _("Total number of Unique household Using Improved Sanitation")

    @classmethod
    def _value(cls, period, data_in):
        return SanitationReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end),\
                toilet_lat__in=improved)\
            .latest_for_patient().distinct()\
            .count()


class ImprovedSanitationDontshare(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "improvedSanitationdontshare"
    short_name  = _("#Using Improved Sanitation dont share")
    long_name   = _("Total number of Unique household Using Improved " \
                    "Sanitation and dont share")

    @classmethod
    def _value(cls, period, data_in):
        return SanitationReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end),\
                toilet_lat__in=improved, \
                share_toilet=share)\
            .latest_for_patient().distinct()\
            .count()

         
class UniqueOneEightyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique_oneeighty_days"
    short_name  = _("Uniq. Sanitation Report 180d")
    long_name   = _("Total number of Sanitation to unique households "\
                    "in the 180 days ending at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return SanitationReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(180))\
            .values('encounter__patient')\
            .distinct()\
            .count()
