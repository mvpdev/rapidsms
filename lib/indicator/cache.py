
import cPickle

from datetime import datetime, date

from hashlib import sha1

from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

from percentage import Percentage
from query_set_type import QuerySetType

STR_FUNCTIONS = {
    int:            str,
    float:          str,
    datetime:       str,
    date:           str,
    bool:           str,
    dict:           str,
}
"""A mapping of a type => function to
use to turn an object of this type
into a cache key
"""

CACHEABLE_TYPES = (int, float, datetime, \
    date, bool, Percentage, dict)
"""Indicator output types that can be cached."""


def cache_simple(func, timeout=60*60*2):
    """
    :func:`cache_simple` is a decorator 
    for caching a function of a single
    argument that returns a pickle-able
    object
    """

    def x(self):
        cache_key = "Simple"+str(func.__name__)

        # Look for the value in the cache
        cached = cache.get(cache_key)

        # Simple value is in the cache
        if cached is not None:
            # "Got cached value!"
            # Cached value is a list of pks
            return cached
            
        # Value is not in the cache
        # so generate the value
        cache_val = func(self)
        if cache_val is None:
            raise ValueError(_("Cannot cache function that returns a value "\
                                "of None"))

        # Get the pks in this queryset and pickle them
        cache.set(cache_key, cache_val, timeout)

        return cache_val
    return x

def cache_indicator(cls, ind_func, period, data_in):
    """
    :func:`cache_indicator` is the function used
    to cache return values of :class:`indicator.indicator.Indicator`.

    :param cls: Indicator to cache
    :type cls: subclass of :class:`indicator.indicator.Indicator`
    :param ind_func: Function which generates the indicator value
    :type ind_func: `function`
    :param period: The time period with which to compute the
                   indicator value
    :param data_in: The input data to the indicator

    """


    # First, make sure we want to execute the caching logic
    if not cls.cache:
        # "skipping cache"
        return ind_func(period, data_in)

    if not cls.type_out in CACHEABLE_TYPES:
        raise TypeError(_("Indicator with output type %s cannot be cached") % \
                        str(cls.type_out))


    # Get the cache key from the function and arguments
    cache_key_elms = [str(cls), cls.slug, \
        str(period.start), str(period.end)]

    if isinstance(cls.type_in, QuerySetType):
        cache_key_elms.append("QuerySet")
        cache_key_elms.append(str(type(data_in)))
        cache_key_elms.append(str(data_in.model))
   
        #cache_key_elms += [str(p[0]) for p in \
        #    data_in.order_by('pk').values_list('pk')]
        cache_key_elms.append(repr(str(data_in.query)))

    else:
        cache_key_elms.append("Other")

        func = STR_FUNCTIONS[cls.type_in]
        cache_key_elms.append(func(data_in))

    s = sha1()
    for e in cache_key_elms:
        s.update(e)

    cache_key = s.hexdigest()

    # Look for a cached value
    cached = cache.get(cache_key)
    if cached is not None:
        # "Got cached indicator"
        return cached

    
    cache_val = ind_func(period, data_in)
    if cache_val is None:
        raise ValueError(_("Cannot cache function that returns a value "\
                            "of None"))

    # "Saving in %s=%s" % (cache_key, str(cache_val))
    cache.set(cache_key, cache_val, cls.valid_for)

    return cache_val

