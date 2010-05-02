#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

"""
Models collection to manage Specimen Referral system statuses and results.
All models rely on the django_tracking application.
"""

from django.db import models
from django_tracking.models import TrackedItem

from reporters.models import Reporter

from findtb.models import FtbState, Specimen


class Sref(FtbState):
    """
    Common parent extended by all models in SREF 
    """
    class Meta:
        app_label = 'findtb'

    specimen = models.ForeignKey(Specimen)

    def get_web_form(self):
        """
        Returns a web form to be shown in the website when this is the current
        state.
        """
        return None


    def get_short_message(self):
        """
        Returns a short description (unicode) of the current specimen state.
        """
        raise NotImplemented


    def get_long_message(self):
        """
        Returns a detailed description (unicode) of the current specimen state.
        """
        raise NotImplemented



class InvalidState(Sref):

    class Meta:
        app_label = 'findtb'

    INVALID_CHOICES = (
        ('invalid', u"Invalid specimen or result"),
        ('lost', u"Lost"),
        ('voided', u"Voided at DTU")
    )

    cause = models.CharField(max_length=10, choices=INVALID_CHOICES)
    new_requested = models.BooleanField(default=True)
    state_type = 'cancel'

    def get_web_form(self):
        pass

    def get_short_message(self):
        return u"Invalidated: %(type)" % {'type': self.type}

    def get_long_message(self):
        return u"%(dtu)s - Specimen for patient %(patient)s invalidated: " \
               u"%(reason)s" % {'dtu': self.specimen.location, \
                                'patient': self.specimen.patient}


class SpecimenRegistered(Sref):
    """
    Proxy class for specimen sample state to be used after a specimen has been
    registered, but before it has been sent. The next state can be
    SpecimenSent or SpecimenCanceled.
    """
    
    class Meta:
        app_label = 'findtb'

    def get_web_form(self):
        pass


    def get_short_message(self):
        return u"Registered with tracking tag %(tag)s" % \
                                    {'tag': self.specimen.tracking_tag}

    def get_long_message(self):
        return u"%(dtu)s - Specimen registered for patient %(patient)s " \
               u"with tracking tag %(tag)s." % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tag': self.specimen.tracking_tag}


class SpecimenSent(Sref):
    """
    Proxy class for specimen sample state to be used after a specimen has been
    sent, but before it has been received. The next state can be
    SpecimenReceived or SpecimenLost.
    """
    class Meta:
        app_label = 'findtb'

    SENDING_METHOD_POST = 'post'
    SENDING_METHOD_ZTLS = 'ztls'
    SENDING_METHOD_OTHER = 'other'

    SENDING_METHOD_CHOICES = (
        (SENDING_METHOD_POST, u"Post"),
        (SENDING_METHOD_ZTLS, u"ZTLS"),
        (SENDING_METHOD_OTHER, u"Other"))

    sending_method = models.CharField(max_length=20, \
                                      choices=SENDING_METHOD_CHOICES)

    def __init__(self, *arg, **kwargs):
        Sref.__init__(self,  *args, **kwargs)
        #super(SpecimenSent, self).__init__(*arg, **kwargs)


    def save(self, *arg, **kwargs):
        Sref.__save__(self, *args, **kwargs)
        #super(SpecimenSent, self).__init__(*arg, **kwargs)

    def get_short_message(self):
        return u"Registered with tracking tag %(tag)s" % \
                                    {'tag': self.specimen.tracking_tag}

    def get_long_message(self):
        # If the method is set to other, the note of the state must include
        # a description of the 'other' sending method.
        if self.sending_method == self.SENDING_METHOD_OTHER:
           return u"%(dtu)s - Specimen for patient %(patient)s " \
                  u"sent. See notes for sending method." % \
                   {'dtu': self.specimen.location, \
                    'patient': self.specimen.patient}
        
        return u"%(dtu)s - Specimen for patient %(patient)s " \
               u"sent through the %(method)s." % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'method': self.get_sending_method_display()}


class SpecimenReceieved(Sref):
    """
    Proxy class for specimen sample state to be used when a specimen has been
    received at NTRL.
    """
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

