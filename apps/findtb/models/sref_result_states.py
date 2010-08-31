#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from dateutil.relativedelta import relativedelta
import datetime
from sref_generic_states import Sref, AlertForBeingLate
from django_tracking.models import TrackedItem

from django.db import models

from celery.registry import tasks
from celery.decorators import task



class MicroscopyResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    tested with microscopy.
    """

    RESULT_CHOICES = [('negative', u"Negative")]
    RESULT_CHOICES.extend(('%d+' % i, u"%d+" % i) for i in xrange(1, 4))
    RESULT_CHOICES.extend(('%d AFB' % i, u"%d AFB" % i) for i in xrange(1, 20))
    RESULT_CHOICES.append(('invalid', u"Invalid"))

    RESULT_CHOICES = tuple(RESULT_CHOICES)

    result = models.CharField(max_length=10, choices=RESULT_CHOICES)

    state_name = 'microscopy'
    state_type = 'result'

    class Meta:
        app_label = 'findtb'

    @task()
    def mgit_reminder(self):
        """ Check if MGIT is late and alert if it is. """
        try:
            s = Specimen.objects.get(pk=self.specimen.pk)
        except Specimen.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=s)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = MgitIsLate(specimen=s)
                state.save()
                ti.state = state
                ti.save()
    tasks.register(mgit_reminder)

    @task()
    def lpa_reminder(self):
        """ Check if LPA is late and alert if it is. """
        try:
            s = Specimen.objects.get(pk=self.specimen.pk)
        except Specimen.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=s)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = LpaIsLate(specimen=s)
                state.save()
                ti.state = state
                ti.save()
    tasks.register(lpa_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """
        if not self.pk:
            if self.is_positive():
                delay = LpaIsLate.get_deadline()
                self.lpa_reminder.apply_async(eta=delay, args=(self,))
            else:
                delay = MgitIsLate.get_deadline()
                self.mgit_reminder.apply_async(eta=delay, args=(self,))

        super(MicroscopyResult, self).save(*args, **kwargs)


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
        ('invalid', u"Invalid")
    )

    result = models.CharField(max_length=10, choices=RESULT_CHOICES)

    state_name = 'mgit'
    state_type = 'result'

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        if self.specimen.should_shortcut_test_flow() and self.result != 'positive':
            # we import it here to avoid circular reference
            from findtb.forms.sref_result_forms import LjForm
            return LjForm

        from findtb.forms.sref_result_forms import SireForm
        return SireForm


    def get_short_message(self):
        return u"MGIT result: %s" % self.get_result_display()


    def get_long_message(self):
        return u"MGIT result for specimen of %(patient)s with "\
               u"tracking tag %(tag)s: %(result)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.get_result_display()}




class LpaResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    tested with LPA.
    """

    state_name = 'lpa'
    state_type = 'result'
    is_final = False

    RIF_CHOICES = (
        ('resistant', u"RIF Resistant") ,
        ('susceptible', u"RIF Susceptible"),
        ('na', u"N/A"),
    )

    INH_CHOICES = (
        ('resistant', u"INH Resistant") ,
        ('susceptible', u"INH Susceptible"),
        ('na', u"N/A"),
    )


    rif = models.CharField(max_length=15, choices=RIF_CHOICES)
    inh = models.CharField(max_length=15, choices=INH_CHOICES)

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        from findtb.forms.sref_result_forms import LjForm
        return LjForm


    def get_short_message(self):
        return u"LPA results: INH %(inh)s and RIF %(rif)s." % {
               'inh': self.inh,
               'rif': self.rif}


    def get_long_message(self):
        return u"LPA results for specimen of %(patient)s with "\
               u"tracking tag %(tag)s: INH %(inh)s and RIF %(rif)s." % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'inh': self.inh,
               'rif': self.rif}



class LjResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    used for LJ.
    """

    state_name = 'lj'
    state_type = 'result'
    is_final = False

    RESULT_CHOICES = (
        ('positive', u"Positive"),
        ('negative', u"Negative"),
        ('invalid', u"Invalid")
    )

    result = models.CharField(max_length=10, choices=RESULT_CHOICES)


    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        from findtb.forms.sref_result_forms import SirezForm
        return SirezForm


    def get_short_message(self):
        return u"LJ result: %s" % self.get_result_display()


    def get_long_message(self):
        return u"LJ result for specimen of %(patient)s with "\
               u"tracking tag %(tag)s: %(result)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.get_result_display()}



class SirezResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    tested with SIREZ.
    """

    state_name = 'sirez'
    state_type = 'result'
    is_final = False

    RIF_CHOICES = (
        ('resistant', u"RIF Resistant") ,
        ('susceptible', u"RIF Susceptible"),
        ('invalid', u"Invalid"),
    )

    INH_CHOICES = (
        ('resistant', u"INH Resistant") ,
        ('susceptible', u"INH Susceptible"),
        ('invalid', u"Invalid"),
    )

    STR_CHOICES = (
        ('resistant', u"STR Resistant") ,
        ('susceptible', u"STR Susceptible"),
        ('invalid', u"Invalid"),
    )

    EMB_CHOICES = (
        ('resistant', u"EMB Resistant") ,
        ('susceptible', u"EMB Susceptible"),
        ('invalid', u"Invalid"),
    )

    PZA_CHOICES = (
        ('untested', u"PZA Untested"),
        ('resistant', u"PZA Resistant"),
        ('susceptible', u"PZA Susceptible"),
        ('invalid', u"Invalid"),
    )

    rif = models.CharField(max_length=15, choices=RIF_CHOICES)
    inh = models.CharField(max_length=15, choices=INH_CHOICES)
    str = models.CharField(max_length=15, choices=STR_CHOICES)
    emb = models.CharField(max_length=15, choices=EMB_CHOICES)
    pza = models.CharField(max_length=15, choices=PZA_CHOICES)

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        None


    def get_short_message(self):
        tests = ('rif', 'inh', 'str', 'emb', 'pza')
        results = ", ".join(test.upper() for test in tests if getattr(self, test) == "resistant")
        return u"SIREZ shows resistance for: %s" % (results or "Nothing")


    def get_long_message(self):
        tests = ('rif', 'inh', 'str', 'emb', 'pza')
        results = ", ".join(test.upper() for test in tests if getattr(self, test) == "resistant")
        return u"SIREZ for specimen of %(patient)s with "\
               u"tracking tag %(tag)s shows resitance for: %(result)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': (results or "Nothing")}


class MgitIsLate(AlertForBeingLate, MicroscopyResult):
    """
    State declaring that the MgitTest is not complete.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+45)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because SpecimenReceived does and we inherit
          from it. This is just a reset to prevent recursive calls.
        """
        super(MicroscopyResult, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"MGIT is late. "\
               u"The deadline was %(deadline)s." % {
               'deadline': self.formated_deadline}


    def get_long_message(self):
        return u"%(dtu)s - MGIT test of specimen for specimen %(patient)s " \
               u"is late: deadline was %(deadline)s." % {
               'dtu': self.specimen.location, 
               'patient': self.specimen.patient, 
               'deadline': self.formated_deadline}


class LpaIsLate(AlertForBeingLate, MicroscopyResult):
    """
    State declaring that the MgitTest is not complete.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+8)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because SpecimenReceived does and we inherit
          from it. This is just a reset to prevent recursive calls.
        """
        super(MicroscopyResult, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"LPA test is late. "\
               u"The deadline was %(deadline)s." % {
               'deadline': self.formated_deadline}


    def get_long_message(self):
        return u"%(dtu)s - LPA test of specimen for specimen %(patient)s " \
               u"is late: deadline was %(deadline)s." % {
               'dtu': self.specimen.location, 
               'patient': self.specimen.patient, 
               'deadline': self.formated_deadline}

