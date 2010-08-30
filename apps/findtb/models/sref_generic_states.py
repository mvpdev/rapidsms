#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

"""
Models collection to manage Specimen Referral system statuses and results.
All models rely on the django_tracking application.
"""

import datetime

from dateutil.relativedelta import relativedelta

from django.db import models

from celery.registry import tasks
from celery.decorators import task

from findtb.models.models import Specimen
from findtb.models.ftbstate import FtbState

from django_tracking.models import TrackedItem

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

        return u"Specimen must be replaced: waiting for a new one"


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

    @task()
    def sending_reminder(self):
        """ Check if the sending is late, send a reminder if it is """
        try:
            s = Specimen.objects.get(pk=self.specimen.pk)
        except Specimen.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=s)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = SendingIsLate(specimen=s)
                state.save()
                ti.state = state
                ti.save()
                msg = u"Specimen for patient %(patient)s (tracking tag " \
                      u"%(tag)s) was registered 2 days ago but has not been "\
                      u"sent. Please send or void." % \
                       {'tag': self.specimen.tracking_tag.upper(),
                        'patient': self.specimen.patient}
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_dtu
                send_to_dtu(s.location, msg)
                
    tasks.register(sending_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """
        if not self.pk:
            delay = SendingIsLate.get_deadline()
            self.sending_reminder.apply_async(eta=delay, args=(self,))
        
        super(SpecimenRegistered, self).save(*args, **kwargs)


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
                                      
    @task()
    def delivery_reminder(self):
        """ Check if speciment delivery is late and send sms if it is. """
        try:
            s = Specimen.objects.get(pk=self.specimen.pk)
        except Specimen.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=s)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = DeliveryIsLate(specimen=s)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_lab_techs,\
                                              send_to_dtls
                send_to_lab_techs(s.location, msg)
                send_to_dtls(s.location, msg)
    tasks.register(delivery_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """
        if not self.pk:
            delay = DeliveryIsLate.get_deadline()
            self.delivery_reminder.apply_async(eta=delay, args=(self,))

        super(SpecimenSent, self).save(*args, **kwargs)
        

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


    @task()
    def microscopy_reminder(self):
        """ Check if speciment microscopy is late and alert if it is. """
        try:
            s = Specimen.objects.get(pk=self.specimen.pk)
        except Specimen.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=s)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = MicroscopyIsLate(specimen=s)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_lab_techs,\
                                              send_to_ztls,\
                                              send_to_dtls
                send_to_lab_techs(s.location, msg)
                send_to_dtls(s.location, msg)
                send_to_ztls(s.location, msg)
    tasks.register(microscopy_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """
        if not self.pk:
            delay = MicroscopyIsLate.get_deadline()
            self.microscopy_reminder.apply_async(eta=delay, args=(self,))
        
        super(SpecimenReceived, self).save(*args, **kwargs)


    def get_web_form(self):

        if self.specimen.should_shortcut_test_flow():
            # we import it here to avoid circular reference
            from findtb.forms.sref_result_forms import MgitForm
            return MgitForm

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
 

class AlertForBeingLate(object):
    """
    Common code to share between alerts triggered when a process is late.
    """    
    delay = relativedelta(weeks=+1)
    state_type = 'alert'
    
    
    @classmethod
    def get_deadline(cls, specimen=None):
        """
        Returns the date when this process was due.
        """
        if specimen:
            ti, c = TrackedItem.get_tracker_or_create(content_object=specimen)
            last_state_date = ti.get_history().exclude(type='alert')[0].created
        else:
            last_state_date = datetime.datetime.today()
        return last_state_date + cls.delay
    
    
    def _formated_deadline(self):
        """
        Get the deadline in a readable format
        """
        d = self.get_deadline(self.specimen)
        return d.strftime('%B %d')
    formated_deadline = property(_formated_deadline)


class SendingIsLate(AlertForBeingLate, SpecimenRegistered):
    """
    State declaring the specimen hasn't been delivered to NTRL for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+2)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because SpecimenSent does and we inherit
          from it. This is just a reset to prevent recursive calls.
        """
        super(SpecimenRegistered, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Specimen registered but late being sent."


    def get_long_message(self):
        return u"%(dtu)s- Specimen for patient %(patient)s " \
               u"was registered but has not been sent. " % {
               'dtu': self.specimen.location, 
               'patient': self.specimen.patient}
                
                
                
class DeliveryIsLate(AlertForBeingLate, SpecimenSent):
    """
    State declaring the specimen hasn't been delivered to NTRL for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+2)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because SpecimenSent does and we inherit
          from it. This is just a reset to prevent recursive calls.
        """
        super(SpecimenSent, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Specimen is late for delivery: delivery was expected by "\
               u"%(deadline)s." % {'deadline': self.formated_deadline}


    def get_long_message(self):
        return u"%(dtu)s - Specimen for patient %(patient)s " \
               u"is late: delivery was expected by %(deadline)s." % {
               'dtu': self.specimen.location, 
               'patient': self.specimen.patient, 
               'tag': self.specimen.tracking_tag.upper(),
               'deadline': self.formated_deadline}
              
              
              
class MicroscopyIsLate(AlertForBeingLate, SpecimenReceived):
    """
    State declaring the specimen hasn't been tested with microscopy for more 
    48h.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+1)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because SpecimenReceived does and we inherit
          from it. This is just a reset to prevent recursive calls.
        """
        super(SpecimenReceived, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Microscopy is late. "\
               u"The deadline was %(deadline)s." % {
               'deadline': self.formated_deadline}


    def get_long_message(self):
        return u"%(dtu)s - Microscopy of specimen for patient %(patient)s " \
               u"is late: deadline was %(deadline)s." % {
               'dtu': self.specimen.location, 
               'patient': self.specimen.patient, 
               'tag': self.specimen.tracking_tag.upper(),
               'deadline': self.formated_deadline}                      
