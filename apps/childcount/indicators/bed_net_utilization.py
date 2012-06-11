'''
Bed net utilization
'''

from django.db.models import F, Q
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import BednetUtilization

from childcount.indicators import registration

NAME = _("Bed Net Utilization")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Bed Net Util. Reports")
    long_name   = _("Total number of bed net utiliaztion reports " \
                    "for unique households during this period")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilization\
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

class Children(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "children"
    short_name  = _("# Kids")
    long_name   = _("Total number of children monitored this period " \
                    "for bed net utilization")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilization\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .aggregate(total=Sum('child_underfive'))['total'] or 0

class ChildrenUsing(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "children_using"
    short_name  = _("# Kids Using")
    long_name   = _("Total number of kids using a "\
                    "bed net this period")

    @classmethod
    def _value(cls, period, data_in):
        return BednetUtilization\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .aggregate(total=Sum('child_lastnite'))['total'] or 0

class ChildrenUsingPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "children_using_perc"
    short_name  = _("% Kids Using Net")
    long_name   = _("Percentage of under fives monitored "\
                    "who used bed nets")
    cls_num     = ChildrenUsing
    cls_den     = Children


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
        return BednetUtilization\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(180))\
            .values('encounter__patient')\
            .distinct()\
            .count()

