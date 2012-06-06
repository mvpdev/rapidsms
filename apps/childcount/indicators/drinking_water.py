'''
Drinking Water Report
'''

from datetime import timedelta

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import DrinkingWaterReport

NAME = _("Drinking Water")

improved = [DrinkingWaterReport.PIPED_WATER,
            DrinkingWaterReport.PUBLIC_TAP_STANDPIPE,
            DrinkingWaterReport.PROTECTED_DUG_WELL,
            DrinkingWaterReport.TUBEWELL_BOREHOLE,
            DrinkingWaterReport.PROTECTED_SPRING,
            DrinkingWaterReport.RAIN_COLLECTION]

treat = DrinkingWaterReport.TREAT_YES


class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Total number of drinking water reports")

    @classmethod
    def _value(cls, period, data_in):
        return DrinkingWaterReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .count()

class UniqueHousehold(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "drinkingwater"
    short_name  = _("Unique Drinking Water Reports")
    long_name   = _("Total number of Unique Drinking Water reports")

    @classmethod
    def _value(cls, period, data_in):
        return DrinkingWaterReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class UsingImprovedDrinkingWater(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "improvedwater"
    short_name  = _("Using Improved Drinkin Water")
    long_name   = _("Total number of Unique household Using Improved " \
                    "Drinking Water")

    @classmethod
    def _value(cls, period, data_in):
        return DrinkingWaterReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end),\
                water_source__in=improved)\
            .latest_for_patient().distinct()\
            .count()


class TreatWater(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "treatwater"
    short_name  = _("Treat Water")
    long_name   = _("Total number of Unique household Treating Water ")

    @classmethod
    def _value(cls, period, data_in):
        return DrinkingWaterReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end),\
                treat_water=treat)\
            .latest_for_patient().distinct()\
            .count()


class UniqueOneEightyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique_oneeighty_days"
    short_name  = _("Uniq. Drinking Water Report 180d")
    long_name   = _("Total number of Drinking Water to unique households "\
                    "in the 180 days ending at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return DrinkingWaterReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(180))\
            .values('encounter__patient')\
            .distinct()\
            .count()
