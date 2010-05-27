#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from sref_generic_states import Sref
from django_tracking.models import TrackedItem

from django.db import models



class MicroscopyResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    tested with microscopy.
    """
    result_list = []
    result_list.append(('negative', u"Negative"))
    for i in range(1, 4):
        result_list.append(('%d+' % i, u"%d+" % i))
    for i in range(1, 20):
        result_list.append(('%d AFB' % i, u"%d AFB" % i))
    result_list.append(('invalid', u"Invalid"))

    RESULT_CHOICES = tuple(result_list)

    result = models.CharField(max_length=10, choices=RESULT_CHOICES)

    state_name = 'microscopy'

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):

        from findtb.forms.sref_result_forms import MgitForm, LpaForm

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        if ti.state.content_object.is_positive():
            return LpaForm

        return MgitForm

    def is_positive(self):
        return self.result != 'negative' and self.result != 'invalid'


    def get_short_message(self):
        return u"Microscopy result: %s" % self.get_result_display()


    def get_long_message(self):
        return u"Microscopy result for specimen of %(patient)s with "\
               u"tracking tag %(tag)s: %(result)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.get_result_display()}



class MgitResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    used for MGIT.
    """

    RESULT_CHOICES = (
        ('positive', u"Positive"),
        ('negative', u"Negative"),
    )

    result = models.CharField(max_length=10, choices=RESULT_CHOICES)

    state_name = 'mgit'

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):

        pass


    def get_short_message(self):
       return u"Received at NTRL"


    def get_long_message(self):
        return u"Received specimen TC#%(tc_number)s, patient %(patient)s " \
                "from %(dtu)s" % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tc_number': self.specimen.tc_number}



class LpaResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    tested with microscopy.
    """

    state_name = 'lpa'

    RIF_CHOICES = (
        ('resistant', u"RIF Resistant") ,
        ('susceptible', u"RIF suceptible"),
        ('na', u"N/A"),
    )

    INH_CHOICES = (
        ('resistant', u"INH Resistant") ,
        ('susceptible', u"INH suceptible"),
        ('na', u"N/A"),
    )


    rif = models.CharField(max_length=15, choices=RIF_CHOICES)
    inh = models.CharField(max_length=15, choices=INH_CHOICES)

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):

        pass


    def get_short_message(self):
       return u"Received at NTRL"


    def get_long_message(self):
        return u"Received specimen TC#%(tc_number)s, patient %(patient)s " \
                "from %(dtu)s" % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tc_number': self.specimen.tc_number}
