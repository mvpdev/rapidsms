
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import Percentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import NeonatalReport

from childcount.indicators import birth

NAME = _("Neonatal")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Number of neonatal reports")

    @classmethod
    def _value(cls, period, data_in):
        return NeonatalReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .values('encounter__patient').distinct()\
            .count()
                

class WithinSevenDaysOfBirth(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "within_seven_days_of_birth"
    short_name  = _("w/in 7d")
    long_name   = _("Number of neonatal reports submitted within "\
                    "seven days of birth for patients born "
                    "during this period")

    @classmethod
    def _value(cls, period, data_in):
        return NeonatalReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__patient__dob__range=(period.start, period.end))\
            .encounter_age(1,7)\
            .values('encounter__patient').distinct()\
            .count()

class WithinSevenDaysOfBirthPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    type_out    = Percentage

    slug        = "within_seven_days_of_birth_perc"
    short_name  = _("% w/in 7d")
    long_name   = _("Percentage of neonatal reports submitted within "\
                    "seven days of birth for patients born during this "
                    "period")

    cls_num     = WithinSevenDaysOfBirth
    cls_den     = birth.Total


