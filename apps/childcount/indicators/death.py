import types

from django.utils.translation import ugettext as _
from django.db import connection

from indicator import Indicator
from indicator import QuerySetType

from childcount.models.reports import DeathReport
from childcount.models import DeadPerson
from childcount.models import Patient

def _deaths_in(period, data_in, days_min, days_max):
    if data_in.count() == 0:
        return 0

    # This is a bit of a hack... we use the
    # encounter__patient__dob__isnull line
    # to force Django to join in the cc_patient table
    # so that we can do our fancy WHERE statement
    d1 = DeathReport\
        .objects\
        .filter(encounter__patient__in=data_in,\
            death_date__range=(period.start, period.end),
            encounter__patient__dob__isnull=False)\
        .extra(where=["DATEDIFF(`death_date`,`cc_patient`.`dob`) BETWEEN %f AND %f" \
                            % (days_min, days_max)])\
        .count()

    d2 = DeadPerson\
        .objects\
        .filter(dod__range=(period.start, period.end),\
            household__in=data_in)\
        .extra(where=["DATEDIFF(`dod`,`dob`) BETWEEN %f AND %f" % (days_min, days_max)])\
        .count()

    return d1+d2

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# Deaths")
    long_name   = _("Total number of patients who died during this period")

    @classmethod
    def _value(cls, period, data_in):
        # The number of people who died aged between 0 
        # and 200 years old
        return _deaths_in(period, data_in, 0, 365*200)

class LocationUnknown(Indicator):
    type_in     = types.NoneType
    type_out    = int

    slug        = "location_unknown"
    short_name  = _("# No loc. Deaths")
    long_name   = _("Total number of patients who died during this period "\
                    "in an unknown location")

    @classmethod
    def _value(cls, period, data_in):
        return DeadPerson\
            .objects\
            .filter(dod__range=(period.start, period.end),\
                household__isnull=True)\
            .count()

class Neonatal(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "neonatal"
    short_name  = _("Deaths < 28d")
    long_name   = _("Total number of neonatal patients "\
                    "who died during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _deaths_in(period, data_in, 0, 28)

class UnderOne(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_one"
    short_name  = _("Deaths < 1y")
    long_name   = _("Total number of under-one patients "\
                    "who died during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _deaths_in(period, data_in, 0, 365)

class UnderFive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five"
    short_name  = _("Deaths < 5y")
    long_name   = _("Total number of under-five patients "\
                    "who died during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _deaths_in(period, data_in, 0, 5*365.25)

class OverFive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "over_five"
    short_name  = _("Deaths >= 5y")
    long_name   = _("Total number of over-five patients "\
                    "who died during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _deaths_in(period, data_in, (5*365.25)+0.01, 200*365.25)


