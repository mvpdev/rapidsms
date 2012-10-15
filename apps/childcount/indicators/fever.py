
from django.db.models.aggregates import Count

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import FeverReport

from childcount.indicators import danger_signs

NAME = _("Fever")


def _fever_reports(period, data_in):
    return FeverReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))


class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Total number of fever reports")

    @classmethod
    def _value(cls, period, data_in):
        return _fever_reports(period, data_in).count()


class RdtPositive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "rdt_postive"
    short_name  = _("RDT+")
    long_name   = _("Fever reports with a positive RDT result")

    @classmethod
    def _value(cls, period, data_in):
        return _fever_reports(period, data_in)\
            .filter(rdt_result=FeverReport.RDT_POSITIVE)\
            .count()


class RdtPositivePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "rdt_postive_perc"
    short_name  = _("% RDT+")
    long_name   = _("Percentage of fever reports with a "\
                    "positive RDT result")

    cls_num     = RdtPositive
    cls_den     = Total


def _rdt_value_given_antimalarial(period, data_in, value):
    values = [v[0] for v in FeverReport.RDT_CHOICES]
    if value not in values:
        raise ValueError(_("%(v)s is not a legal RDT result value") % \
                            {'v': value})

    return _fever_reports(period, data_in)\
        .filter(rdt_result=value,\
            encounter__ccreport__medicinegivenreport__medicines__code='ACT')


class RdtPositiveGivenAntimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "rdt_postive_given_antimalarial"
    short_name  = _("RDT+ w/ ACT")
    long_name   = _("Fever reports with a positive RDT result "\
                    "where the patient was given antimalarials")

    @classmethod
    def _value(cls, period, data_in):
        return _rdt_value_given_antimalarial(period, \
                            data_in, FeverReport.RDT_POSITIVE).count()


class RdtPositiveGivenAntimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "rdt_postive_given_antimalarial"
    short_name  = _("RDT+ w/ ACT")
    long_name   = _("Fever reports with a positive RDT result "\
                    "where the patient was given antimalarials")

    @classmethod
    def _value(cls, period, data_in):
        return _rdt_value_given_antimalarial(period,\
            data_in, FeverReport.RDT_POSITIVE).count()


def _under_five_rdt(period, data_in):
    return _fever_reports(period, data_in).encounter_under_five()


class UnderFiveRdtPositiveGivenAntimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_rdt_postive_given_antimalarial"
    short_name  = _("U5 RDT+ w/ ACT")
    long_name   = _("Fever reports for under-fives with a positive RDT result "\
                    "where the patient was given antimalarials")

    @classmethod
    def _value(cls, period, data_in):
        return _rdt_value_given_antimalarial(period, \
                            data_in, FeverReport.RDT_POSITIVE)\
            .encounter_under_five()\
            .count()

"""
class UnderFiveRdtPositiveGivenAntimalarialPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "under_five_rdt_postive_given_antimalarial_perc"
    short_name  = _("% U5 RDT+ w/ ACT")
    long_name   = _("Percentage of under five patients given antimalarials "\
                    "after testing positive with an RDT")

    cls_num     = UnderFiveRdtPositiveGivenAntimalarial
    cls_den     = danger_signs.UnderFiveFeverUncomplicatedRdtPositive
"""


class UnderFiveRdtNegativeGivenAntimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_rdt_negative_given_antimalarial"
    short_name  = _("U5 RDT- w/ ACT")
    long_name   = _("Fever reports for under-fives with a negative RDT result "\
                    "where the patient was given antimalarials")

    @classmethod
    def _value(cls, period, data_in):
        return _rdt_value_given_antimalarial(period, \
                            data_in, FeverReport.RDT_NEGATIVE)\
            .encounter_under_five()\
            .count()


def _over_five_rdt(period, data_in):
    return _fever_reports(period, data_in).encounter_over_five()


class OverFiveRdt(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "over_five_rdt"
    short_name  = _(">5y RDT")
    long_name   = _("RDT results for patients over 5y")

    @classmethod
    def _value(cls, period, data_in):
        return _over_five_rdt(period, data_in).count()


class OverFiveRdtPositive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "over_five_rdt_positive"
    short_name  = _(">5y RDT+")
    long_name   = _("Postiive RDT results for patients over 5y")

    @classmethod
    def _value(cls, period, data_in):
        return _over_five_rdt(period, data_in)\
            .filter(rdt_result=FeverReport.RDT_POSITIVE)\
            .count()


class OverFiveRdtNegative(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "over_five_rdt_negative"
    short_name  = _(">5y RDT-")
    long_name   = _("Negative RDT results for patients over 5y")

    @classmethod
    def _value(cls, period, data_in):
        return _over_five_rdt(period, data_in)\
            .filter(rdt_result=FeverReport.RDT_NEGATIVE)\
            .count()


class OverFiveRdtPositiveGivenAntimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "over_five_rdt_positive_given_antimalarial"
    short_name  = _(">5y RDT+ w/ ACT")
    long_name   = _("Number of postiive RDT results for patients over 5y "\
                    "after which patient was given antimalarials")

    @classmethod
    def _value(cls, period, data_in):
        return _over_five_rdt(period, data_in)\
            .filter(rdt_result=FeverReport.RDT_POSITIVE,\
                encounter__ccreport__medicinegivenreport__medicines__code='ACT')\
            .count()


class OverFiveRdtPositiveGivenAntimalarialPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    
    slug        = "over_five_rdt_positive_given_antimalarial_perc"
    short_name  = _("%Over5 RDT+ w/AM")
    long_name   = _("Percentage of patients over five with a positive "\
                    "RDT result who were given antimalarials")

    cls_num     = OverFiveRdtPositiveGivenAntimalarial
    cls_den     = OverFiveRdtPositive


class OverFiveRdtNegativeGivenAntimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "over_five_rdt_negative_given_antimalarial"
    short_name  = _(">5y RDT- w/ ACT")
    long_name   = _("Number of negative RDT results for patients over 5y "\
                    "after which patient was given antimalarials")

    @classmethod
    def _value(cls, period, data_in):
        return _over_five_rdt(period, data_in)\
            .filter(rdt_result=FeverReport.RDT_NEGATIVE,\
                encounter__ccreport__medicinegivenreport__medicines__code='ACT')\
            .count()


class OverFiveRdtNegativeGivenAntimalarialPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    
    slug        = "over_five_rdt_negative_given_antimalarial_perc"
    short_name  = _("%Over5 RDT- w/AM")
    long_name   = _("Percentage of patients over five with a negative "\
                    "RDT result who were given antimalarials")

    cls_num     = OverFiveRdtNegativeGivenAntimalarial
    cls_den     = OverFiveRdtNegative
