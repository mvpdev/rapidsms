#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import numbers

from percentage import Percentage
from cache import cache_indicator
from query_set_type import QuerySetType

from django.db import connection
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

class Indicator(object):
    type_in     = None
    """Type of the data argument to this indicator.
    Often this will be an instantiated 
    :class:`indicator.query_set_type.QuerySetType`
    like `QuerySetType(Patient)`.
    """

    type_out    = None
    """The type of the return value of this indicator.
    Used to figure out whether or not it can be cached. 
    """

    slug        = None
    """A machine-friendly identifier string for this indicator, 
    using a-z, A-Z, 0-9, and underscore.
    """

    short_name  = None
    """A short human-readable name for this indicator, like
    "% FP".
    """

    long_name   = None
    """A long human-readable name for this indicator, like
    "Percentage of women 15-49 using modern family planning
    methods.
    """

    cache       = True
    """A boolean indicating whether or not this indicator
    should be cached. Should be False for indicators with
    non-pickle-able output values.
    """

    valid_for   = 2*60*60
    """How long to keep cached values for before expiring
    them.
    """

    @classmethod
    def _value(cls, period, data_in):
        """The main indicator function.

        :param period: A time period object, with a :meth:`.start`
                       and an :meth:`.end` method, each of which 
                       returns a :class:`datetime.datetime` object.
        :param data_in: The data parameter for this indicator.
                        Often a QuerySet of patients or CHWs or clinics.
        """
        raise NotImplementedError(_("No value method implemented!"))

    
    # You shouldn't have implement anything below this line
    # in your Indicator subclasses...

    @classmethod
    def input_is_query_set(cls):
        """True if the input type is a :class:`QuerySet` """
        return isinstance(cls.type_in, QuerySetType)

    @classmethod
    def output_is_number(cls):
        """True if the output type is a subclass of 
        :class:`numbers.Number`.
        """
        return issubclass(cls.type_out, numbers.Number)

    @classmethod
    def output_is_percentage(cls):
        """True if the output type is 
        :class:`indicator.percentage.Percentage`.
        """
        return issubclass(cls.type_out, Percentage)

    @classmethod
    def _check_type(cls, expected, value, s):
        if cls.slug is None:
            raise ValueError(_("Indicator slug cannot be None"))

        if expected is QuerySet:
            raise TypeError(_("Expected %(str)s type cannot be a QuerySet. "\
                            "Use an indicator.QuerySetType object instead.") % \
                            {'str': s})

        # First, check if we're dealing with a QuerySetType object
        if isinstance(expected, QuerySetType):
            if not isinstance(value, QuerySet):
                raise TypeError(_("Expected %(str)s type %(exp)s but got illegal " \
                                    "%(str)s type %(ill)s!") % \
                                    {'exp': QuerySet, 'ill': type(value), 'str': s})

            if value.model is not expected.mtype:
                raise TypeError(_("Expected %(str)s QuerySet of type %(exp)s but got illegal " \
                                    "%(str)s QuerySet of type %(ill)s!") % \
                                    {'exp': expected.mtype, 'ill': value.model, 'str': s})

        # If we don't have a QuerySetType, then just do regular type checking
        else:
            if not isinstance(value, expected):
                raise TypeError(_("Expected %(str)s type %(exp)s but got illegal " \
                                    "%(str)s type %(ill)s!") % \
                                    {'exp': expected, 'ill': type(value), 'str': s})


    def __new__(cls, period, data_in):
        cls._check_type(cls.type_in, data_in, _("input"))
        print connection.queries
        data_out = cache_indicator(cls, cls._value, period, data_in)
        connection.queries = []
        cls._check_type(cls.type_out, data_out, _("output"))
        return data_out 

class IndicatorPercentage(Indicator):
    """
    Subclass of :class:`indicator.indicator.Indicator` for
    percentage values. You give it the two indicators that
    make up the numerator and denominator values and it 
    gives you back a :class:`indicator.percentage.Percentage`.
    """

    cls_num = None
    """The numerator :class:`indicator.indicator.Indicator`"""
    cls_den = None
    """The denominator :class:`indicator.indicator.Indicator`"""

    type_out = Percentage

    @classmethod
    def _value(cls, period, data_in):
        return Percentage(cls.cls_num(period, data_in), cls.cls_den(period, data_in))

class IndicatorDifference(Indicator):
    """
    Subclass of :class:`indicator.indicator.Indicator` for
    difference values. You give it the two indicators that
    make up the numerator and denominator values and it 
    gives you back their difference.
    """
    cls_first   = None
    """The inital :class:`indicator.indicator.Indicator` value"""
    cls_second  = None
    """The number to subtract from the initial
    :class:`indicator.indicator.Indicator` value
    """

    @classmethod
    def _value(cls, period, data_in):
        if cls.cls_first.type_out != cls.cls_second.type_out:
            raise TypeError(_("Cannot compute difference of indicators "\
                                "with unequal types!"))

        return (cls.cls_first(period, data_in) - cls.cls_second(period, data_in))


