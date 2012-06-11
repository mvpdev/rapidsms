'''
BedNetCoverage
'''

from django.db.models import F, Q
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import BedNetReport

from childcount.indicators import registration

NAME = _("Bed Net Coverage")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Bed Net Reports")
    long_name   = _("Total number of bed net coverage reports " \
                    "for unique households during this period")

    @classmethod
    def _value(cls, period, data_in):
        return BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class SleepingSites(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "sleeping_sites"
    short_name  = _("# Sites Seen")
    long_name   = _("Total number of sleeping sites monitored this period")

    @classmethod
    def _value(cls, period, data_in):
        return BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .aggregate(total=Sum('sleeping_sites'))['total'] or 0

class SleepingSitesUniq(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "sleeping_sites_uniq"
    short_name  = _("# Sites")
    long_name   = _("Total number of sleeping sites for unique "\
                    "household monitored this period")

    @classmethod
    def _value(cls, period, data_in):
        return BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .latest_for_patient()\
            .aggregate(total=Sum('sleeping_sites'))['total'] or 0

class SleepingSitesUniqMissing(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "sleeping_sites_uniq_missing"
    short_name  = _("# Sites Unc")
    long_name   = _("Total number of sleeping sites for unique "\
                    "household monitored this period with fewer bed nets "\
                    "than sleeping sites")

    @classmethod
    def _value(cls, period, data_in):
        rpts = BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .latest_for_patient()\
            .filter(function_nets__lt=F('sleeping_sites'),\
                function_nets__isnull=False,\
                sleeping_sites__isnull=False)

        count = 0
        for r in rpts:
            count += max(0, r.sleeping_sites - r.function_nets)

        return count
            
class SleepingSitesUniqMissingPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "sleeping_sites_uniq_missing_perc"
    short_name  = _("% Sites w/o net")
    long_name   = _("Percentage of unique sleeping sites monitored "\
                    "and known to have no bed net")
    cls_num     = SleepingSitesUniqMissing
    cls_den     = SleepingSitesUniq

class Covered(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "covered"
    short_name  = _("# HHs Covered")
    long_name   = _("Total number of unique households monitored "\
                    "and having known bed net coverage this period")

    @classmethod
    def _value(cls, period, data_in):
        return BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end),\
                function_nets__gte=F('sleeping_sites'),\
                function_nets__isnull=False,\
                sleeping_sites__isnull=False)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class Unknown(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unknown"
    short_name  = _("# HHs Bed Net Unknown")
    long_name   = _("Total number of unique households monitored "\
                    "without known bed net coverage")

    @classmethod
    def _value(cls, period, data_in):
        return BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .filter(Q(sleeping_sites__isnull=True)|Q(function_nets__isnull=True))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UnknownOrUncovered(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unknown_or_uncovered"
    short_name  = _("# HHs Bed Net Unknown/Uncovered")
    long_name   = _("Total number of unique households monitored "\
                    "without known bed net coverage or known "\
                    "to be uncovered")
    cls_first   = Total
    cls_second  = Covered

class Uncovered(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "uncovered"
    short_name  = _("# HHs Bed Net Uncovered")
    long_name   = _("Total number of unique households monitored "\
                    "and known to be uncovered")
    cls_first   = UnknownOrUncovered 
    cls_second  = Unknown

class CoveredPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "uncovered_perc"
    short_name  = _("% HHs Bed Net Known Covered")
    long_name   = _("Percentage of unique households monitored "\
                    "and known to be covered with bed nets")
    cls_num     = Covered
    cls_den     = Total


class CoveragePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "coverage_perc"
    short_name  = _("% Known")
    long_name   = _("Percentage of unique households monitored "\
                    "for bed net coverage")

    cls_num     = Total
    cls_den     = registration.Household


class UniqueOneEightyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int
    total_column = False
    
    slug        = "unique_oneeighty_days"
    short_name  = _("Uniq. Household Bednet Coverage reports for 180d")
    long_name   = _("Total number of Bednet Coverage Report to unique households "\
                    "in the 180 days ending at the end of this time period")

    @classmethod
    def _value(cls, period, data_in):
        return BedNetReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gt=period.end - timedelta(180))\
            .values('encounter__patient')\
            .distinct()\
            .count()
