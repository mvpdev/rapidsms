'''
Bed net utilization Pregnancy
'''

from django.db.models import F, Q
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import BednetUtilizationPregnancy

from childcount.indicators import registration

NAME = _("BedNet Utilization Pregnant")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Bed Net Util. Reports")
    long_name   = _("Total number of bed net utiliaztion reports " \
                    "for unique households during this period")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilizationPregnancy\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class CoveragePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "coverage_perc"
    short_name  = _("% Cov")
    long_name   = _("Percentage of households monitored for "\
                    "bed net utilization during this period")
    cls_num     = Total
    cls_den     = registration.Household

class Pregnant(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "pregnant"
    short_name  = _("# pregnant")
    long_name   = _("Total number of Pregnant Women monitored this period " \
                    "for bed net utilization")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilizationPregnancy\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .aggregate(total=Sum('slept_lastnite'))['total'] or 0

class PregnantUsing(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "pregnancy_using"
    short_name  = _("# Pregnancy Using bednet")
    long_name   = _("Total number of Pregnant Women using a "\
                    "bed net this period")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilizationPregnancy\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .aggregate(total=Sum('slept_underbednet'))['total'] or 0

class PregnantUsingPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "pregnant_using_perc"
    short_name  = _("% Pregnant Using Net")
    long_name   = _("Percentage of Pregnant Women monitored "\
                    "who used bed nets")
    cls_num     = PregnantUsing
    cls_den     = Pregnant


class UniqueOneEightyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int
    total_column = False
    
    slug        = "unique_oneeighty_days"
    short_name  = _("Uniq. Bednet Utilization Pregnancy reports for 180d")
    long_name   = _("Total number of Bednet Utilization Pregnancy reports " \
                    "to unique households in the 180 days ending "\
                    " at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilizationPregnancy\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(180))\
            .values('encounter__patient')\
            .distinct()\
            .count()
