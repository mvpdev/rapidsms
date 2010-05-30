#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

"""
Models collection to manage Specimen Referral system statuses and results.
All models rely on the django_tracking application.
"""

from django.db import models

from findtb.models.models import Specimen
from findtb.models.ftbstate import FtbState


class Sref(FtbState):
    """
    Common parent extended by all models in SREF
    """
    class Meta:
        app_label = 'findtb'

    specimen = models.ForeignKey(Specimen)
    state_origin = 'sref'

    STATE_NAMES = ('specimen_registered',
                   'specimen_sent',
                   'specimen_received',
                   'microscopy',
                   'lpa',
                   'lj',
                   'mgit',
                   'sirez')

    form_class = None


    def get_web_form(self):
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



class SpecimenInvalid(Sref):
    """
    Final state used to declare the specimen as invalid or lost.
    """

    class Meta:
        app_label = 'findtb'

    INVALID_CHOICES = (
        ('invalid', u"Invalid specimen or result"),
        ('lost', u"Specimen lost"),
        ('voided', u"Speciment voided at DTU")
    )

    cause = models.CharField(max_length=10, choices=INVALID_CHOICES)
    new_requested = models.BooleanField(default=True)

    state_name = 'invalid'
    state_type = 'cancelled'
    is_final = True


    def get_short_message(self):

        return self.get_cause_display()


    def get_long_message(self):

        cause = self.get_cause_display()
        return u"%(dtu)s - %(cause)s patient for %(patient)s" % {
                                            'dtu': self.specimen.location,
                                            'patient': self.specimen.patient,
                                            'cause': cause }



class SpecimenMustBeReplaced(Sref):
    """
    Final state used to declare the specimen as invalid or lost.
    """

    state_name = 'invalid'

    class Meta:
        app_label = 'findtb'


    next_specimen = models.ForeignKey(Specimen, blank=True, null=True)
    state_type = 'cancelled'
    is_final = True


    def get_short_message(self):

        if self.next_specimen:
            return u"Has been replaced: new specimen is %s" % self.next_specimen

        return u"Must be replaced: waiting for a new one"


    def get_long_message(self):

        if self.next_specimen:
                   return u"%(dtu)s - Specimen for patient %(patient)s have been "\
                          u"replaced: news specimen is %(next)s" %\
                          {'dtu': self.specimen.location,
                            'patient': self.specimen.patient,
                            'next': self.next_specimen}



        return u"%(dtu)s - Specimen for patient %(patient)s must be "\
               u"replaced: waiting for a new one" %\
               {'dtu': self.specimen.location,
                'patient': self.specimen.patient}



class SpecimenRegistered(Sref):
    """
    Model for specimen sample state to be used after a specimen has been
    registered, but before it has been sent. The next state can be
    SpecimenSent or SpecimenCanceled.
    """

    state_type = 'notice'
    state_name = 'incoming'


    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        # we import it here to avoid circular reference
        from findtb.forms.sref_transit_forms import SrefRegisteredReceived
        return SrefRegisteredReceived


    def get_short_message(self):
        return u"Registered with tracking tag %(tag)s" % \
                                    {'tag': self.specimen.tracking_tag }

    def get_long_message(self):
        return u"%(dtu)s - Specimen registered for patient %(patient)s " \
               u"with tracking tag %(tag)s." % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tag': self.specimen.tracking_tag.upper()}



class SpecimenSent(Sref):
    """
    Proxy class for specimen sample state to be used after a specimen has been
    sent, but before it has been received. The next state can be
    SpecimenReceived or SpecimenLost.
    """

    state_name = 'incoming'

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

    def get_web_form(self):
        # we import it here to avoid circular reference
         from findtb.forms.sref_transit_forms import SrefLostOrReceived
         return SrefLostOrReceived


    def get_short_message(self):
        # If the method is set to other, the note of the state must include
        # a description of the 'other' sending method.
        if self.sending_method == self.SENDING_METHOD_OTHER:
           return u'Sent. DTU noted "%s"' % self.note

        return u'Sent throught the %s.' % self.get_sending_method_display()


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



class SpecimenReceived(Sref):
    """
    Proxy class for specimen sample state to be used when a specimen has been
    received at NTRL.
    """

    state_name = 'received'

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        # we import it here to avoid circular reference
        from findtb.forms.sref_result_forms import MicroscopyForm
        return MicroscopyForm


    def get_short_message(self):
       return u"Received at NTRL"


    def get_long_message(self):
        return u"Received specimen TC#%(tc_number)s, patient %(patient)s " \
                "from %(dtu)s" % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tc_number': self.specimen.tc_number}


class AllTestsDone(Sref):

    state_name = 'done'
    state_type = 'checked'
    is_final = True

    class Meta:
        app_label = 'findtb'


    def get_short_message(self):
       return u"All tests for this specimen have been done"


    def get_long_message(self):
        return u"All test for specimen TC#%(tc_number)s, patient %(patient)s " \
                "from %(dtu)s have been done" % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tc_number': self.specimen.tc_number}
