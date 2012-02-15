#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.utils.translation import ugettext as _

class PeriodType(object):
    def __init__(self):
        pass

    title = None
    descripton = None
    n_periods = None

    # Used for storing a reference to this
    # PeriodType in the DB
    code = None
    
    @classmethod
    def periods(cls): 
        raise NotImplementedError


