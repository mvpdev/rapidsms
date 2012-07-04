'''
Registrations
'''

from datetime import timedelta

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient

NAME = _("Registration")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Registered")
    long_name   = _("Total number registered patients")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .count()

class UnderOne(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_one"
    short_name  = _("U1y")
    long_name   = _("Total number registered under-ones")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .under_one(period.start, period.end)\
            .count()


class UnderFive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five"
    short_name  = _("U5y")
    long_name   = _("Total number registered under-fives")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .under_five(period.start, period.end)\
            .count()

class UnderNine(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_nine"
    short_name  = _("U9y")
    long_name   = _("Total number registered under-nines")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .under_nine(period.start, period.end)\
            .count()

class UnderNineMonths(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_nine_months"
    short_name  = _("U9m")
    long_name   = _("Total number registered under nine months")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .under_nine_months(period.start, period.end)\
            .count()


class UnderSixMonths(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_six_months"
    short_name  = _("U6m")
    long_name   = _("Total number registered kids under 6 months of age")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .under_six_months(period.start, period.end)\
            .count()

class MuacEligible(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "muac_eligible"
    short_name  = _("MUACable")
    long_name   = _("Total number registered kids between 6 months and "\
                    "60 months of age")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .muac_eligible(period.start, period.end)\
            .count()

class Household(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "household"
    short_name  = _("HH")
    long_name   = _("Total number registered households")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .household(period.start, period.end)\
            .count()

class Mobile(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "mobile"
    short_name  = _("Mobile")
    long_name   = _("Total registered patients with mobile number")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .created_before(period.end)\
            .alive(period.start, period.end)\
            .exclude(mobile='')\
            .exclude(mobile__isnull=True)\
            .count()


class HasUnderFive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "hasunderfive"
    short_name  = _("Household with Underfive")
    long_name   = _("Total Household with underfive as at period end")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .under_five(period.start, period.end)\
            .values('household')\
            .distinct()

        return data_in.filter(health_id__in=households)\
            .distinct()\
            .count()


class HasPregnancy(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "haspregnancy"
    short_name  = _("Household with Pregnancy")
    long_name   = _("Total Household with Pregnancy as at period end")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .pregnant(period.start, period.end)\
            .values('household')\
            .distinct()

        return data_in.filter(health_id__in=households)\
            .distinct()\
            .count()


class HasNeonatal(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "hasneonatal"
    short_name  = _("Household with Neonatal")
    long_name   = _("Total Household with Neonatal as at period end")

    @classmethod
    def _value(cls, period, data_in):
        households =  data_in\
            .neonatal(period.start, period.end)\
            .values('household')\
            .distinct()

        return data_in.filter(health_id__in=households)\
            .distinct()\
            .count()
