#!/usr/bin/env python
# -*- coding= UTF-8 -*-

"""
Models collection to manage EQA system statuses and results.
All models rely on the django_tracking application.
"""

import datetime

from dateutil.relativedelta import relativedelta

from django.db import models

from celery.registry import tasks
from celery.decorators import task

from django_tracking.models import TrackedItem

from models import SlidesBatch
from ftbstate import FtbState


class Eqa(FtbState):
    """ Common parent extended by all models in EQA """
    
    class Meta:
        app_label = 'findtb'

    slides_batch = models.ForeignKey(SlidesBatch)
    state_origin = 'eqa'
    form_class = None


    def get_web_form(self):
        return None


    def get_short_message(self):
        """
        Returns a short description (unicode) of the current slides state.
        """
        raise NotImplemented


    def get_long_message(self):
        """
        Returns a detailed description (unicode) of the current slides state.
        """
        raise NotImplemented



class EqaStarts(Eqa):
    """
    State declaring the slides are ready to be picked up by the DTLS from the
    DTU.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'eqa_starts'

    @task()
    def dtu_collection_reminder(self):
        """ Check if EQA is late, and if yes trigger and alerts. """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = DtuCollectionIsLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_ztls,\
                                              send_to_dtu_focal_person,\
                                              send_to_dtls
                send_to_dtls(sb.location, msg)
                send_to_ztls(sb.location, msg)
    tasks.register(dtu_collection_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """
        if not self.pk:
            delay = DtuCollectionIsLate.get_deadline()
            self.dtu_collection_reminder.apply_async(eta=delay, args=(self,))
        
        super(EqaStarts, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides are ready to be picked up by DTLS"


    def get_long_message(self):
        return u"Slides from %(dtu)s are ready to be picked up by the DTLS" % {
                                            'dtu': self.slides_batch.location }


class CollectedFromDtu(Eqa):
    """
    State declaring the slides have been collected by DTLS from the DTU.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'collected_from_dtu'
    
    
    @task()
    def controller_delivery_reminder(self):
        """
        If delivery to first controller is late, triggers an alerts.
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = DeliveryToFirstCtrlLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_ztls, send_to_dtls,\
                                              send_to_first_controller
                send_to_first_controller(sb.location, msg)
                send_to_dtls(sb.location, msg)
    tasks.register(controller_delivery_reminder)
    
    
    def save(self, *args, **kwargs):
        """ Setup the alert """
        
        if not self.pk:
            delay = DeliveryToFirstCtrlLate.get_deadline()
            self.controller_delivery_reminder.apply_async(eta=delay, 
                                                          args=(self,))
        
        super(CollectedFromDtu, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"%s slides have been collected by the DTLS from the DTU." %\
               self.slides_batch.slide_set.all().count()


    def get_long_message(self):
        return u"%(number)s slides have been picked up from %(dtu)s by the "\
               u"DTLS" % { 'dtu': self.slides_batch.location.name,
                           'number': self.slides_batch.slide_set.all().count()}



class DeliveredTo1stCtrler(Eqa):
    """
    State declaring the slides have been delivered by DTLS to the 1st
    controller.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'delivered_to_first_controller'
    
    
    @task()
    def first_control_reminder(self):
        """
        If testing by first controller is late, triggers an alert
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = FirstCtrlTestingLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_ztls, send_to_dtls,\
                                              send_to_first_controller
                send_to_first_controller(sb.location, msg)
                send_to_dtls(sb.location, msg)
    tasks.register(first_control_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """

        if not self.pk:
            delay = FirstCtrlTestingLate.get_deadline()
            self.first_control_reminder.apply_async(eta=delay, 
                                                            args=(self,))
        
        super(DeliveredTo1stCtrler, self).save(*args, **kwargs)
        

    def get_short_message(self):
        return u"Slides have been delivered to the first controller"


    def get_long_message(self):
        return u"Slides from %(dtu)s have been delivered to the first "\
               u"controller" % { 'dtu': self.slides_batch.location.name}



class PassedFirstControl(Eqa):
    """ State declaring the slides have been tested by the first controller """

    class Meta:
        app_label = 'findtb'

    state_name = 'passed_first_control'

    @task()
    def controller_collection_reminder(self):
        """
        If collection from first controller is late, triggers an alerts.
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = FirstCtrlCollectionLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_ztls, send_to_dtls,\
                                              send_to_first_controller
                send_to_first_controller(sb.location, msg)
                send_to_dtls(sb.location, msg)
    tasks.register(controller_collection_reminder)


    def save(self, *args, **kwargs):
        """ Setup the alert """

        if not self.pk:
            delay = FirstCtrlCollectionLate.get_deadline()
            self.controller_collection_reminder.apply_async(eta=delay, 
                                                            args=(self,))
        
        super(PassedFirstControl, self).save(*args, **kwargs)
    

    def get_short_message(self):
        return u"Slides have been tested by the first controller"


    def get_long_message(self):
        return u"Slides from %(dtu)s have been tested by the "\
               u"first controller" % {'dtu': self.slides_batch.location.name}


class CollectedFrom1stCtrl(Eqa):
    """
    State declaring the slides have been collected by DTLS from the
    first controller.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'collected_from_first_controller'
    
    
    @task()
    def second_controller_delivery_reminder(self):
        """
        If delivery to second controller is late, triggers an alerts.
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = DeliveryToScndCtrlLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_ztls, send_to_dtls,\
                                              send_to_first_controller
                send_to_first_controller(sb.location, msg)
                send_to_dtls(sb.location, msg)
    tasks.register(second_controller_delivery_reminder)
    
    
    def save(self, *args, **kwargs):
        """ Setup the alert """

        if not self.pk:
            delay = DeliveryToScndCtrlLate.get_deadline()
            self.second_controller_delivery_reminder.apply_async(eta=delay, 
                                                            args=(self,))
        
        super(CollectedFrom1stCtrl, self).save(*args, **kwargs)
        

    def get_short_message(self):
        return u"Slides have been picked up by the DTLS"


    def get_long_message(self):
        return u"Slides from %(dtu)s have been picked up from the first "\
               u"controller by the DTLS" % {
                'dtu': self.slides_batch.location.name}


class DeliveredTo2ndCtrl(Eqa):
    """
    State declaring the slides have been delivered by DTLS to the second
    controller.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'delivered_to_second_controller'

    @task()
    def second_control_reminder(self):
        """
        If second controller is late, triggers an alerts.
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = SecondCtrlTestingLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()

    tasks.register(second_control_reminder)
    
    
    def save(self, *args, **kwargs):
        """ Setup the alert """

        if not self.pk:
            delay = SecondCtrlTestingLate.get_deadline()
            self.second_control_reminder.apply_async(eta=delay, 
                                                            args=(self,))
        
        super(DeliveredTo2ndCtrl, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides have been delivered to the second controller"


    def get_long_message(self):
        return u"Slides from %(dtu)s have been delivered to the "\
               u"second controller" % {'dtu': self.slides_batch.location.name}


class ResultsAvailable(Eqa):
    """ State declaring the results for the slides are available """

    class Meta:
        app_label = 'findtb'

    state_name = 'results_available'
    state_type = 'result'

    @task()
    def second_control_report_late(self):
        """
        If second controller is late in preparing report, triggers an alerts.
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = SecondCtrlReportLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()

    tasks.register(second_control_report_late)
    
    
    def save(self, *args, **kwargs):
        """ Setup the alert """

        if not self.pk:
            delay = SecondCtrlReportLate.get_deadline()
            self.second_control_report_late.apply_async(eta=delay, 
                                                            args=(self,))
        
        super(ResultsAvailable, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"EQA results: %s" % self.slides_batch.results


    def get_long_message(self):
        return u"EQA results for slides from %(dtu)s: %(results)s" % {
                'dtu': self.slides_batch.location.name,
                'results': self.slides_batch.results }
                
                
class ReadyToLeaveNtrl(Eqa):
    """  State declaring the slides are ready to leave NTRL  """

    class Meta:
        app_label = 'findtb'

    state_name = 'ready_to_leave_ntrl'

    @task()
    def receive_by_dtu_reminder(self):
        """
        If acknowledgement of receipt by the DTU is late, triggers an alerts.
        """
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == self.state_name and ti.state.type != 'alert':
                state = ReceivedByDtuLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                # must import here to avoid circular references
                from findtb.libs.utils import send_to_ztls, send_to_dtls,\
                                              send_to_first_controller
                send_to_first_controller(sb.location, msg)
                send_to_dtls(sb.location, msg)
                send_to_ztls(sb.location, msg)
    tasks.register(receive_by_dtu_reminder)
    
    
    def save(self, *args, **kwargs):
        """ Setup the alert """

        if not self.pk:
            delay = ReceivedByDtuLate.get_deadline()
            self.receive_by_dtu_reminder.apply_async(eta=delay, 
                                                            args=(self,))
        
        super(ReadyToLeaveNtrl, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides are ready to be sent back to DTU"


    def get_long_message(self):
        return u"Slides from %(dtu)s are ready to be sent back to DTU" % {
                'dtu': self.slides_batch.location.name}



class ReceivedAtDtu(Eqa):
    """  State declaring have been received at DTU """

    class Meta:
        app_label = 'findtb'

    state_name = 'received_at_dtu'
    state_type = 'checked'
    is_final = True


    def get_short_message(self):
        return u"Slides have arrived at DTU. End of EQA for this quarter."


    def get_long_message(self):
        return u"Slides from %(dtu)s have arrived at DTU" % {
                'dtu': self.slides_batch.location.name}


class AlertForBeingLate(object):
    """
    Common code to share between alerts triggered when a process is late.
    """    
    delay = relativedelta(weeks=+1)
    state_type = 'alert'
    
    
    @classmethod
    def get_deadline(cls, slides_batch=None):
        """
        Returns the date when this process was due.
        """
        if slides_batch:
            ti, c = TrackedItem.get_tracker_or_create(content_object=slides_batch)
            last_state_date = ti.get_history().exclude(type='alert')[0].created
        else:
            last_state_date = datetime.datetime.today()
        return last_state_date + cls.delay
    
    
    def _formated_deadline(self):
        """
        Get the deadline in a readable format
        """
        d = self.get_deadline(self.slides_batch)
        return d.strftime('%B %d')
    formated_deadline = property(_formated_deadline)      
      
      
         
class DtuCollectionIsLate(AlertForBeingLate, EqaStarts):
    """
    State declaring the slides haven't been picked up from DTU for too long.
    """

    class Meta:
        app_label = 'findtb'
        
    
    def save(self, *args, **kwargs):
        """
        We must override it because EqaStarts does and we inherit from it.
        This is just a reset to prevent recursive calls.
        """
        super(EqaStarts, self).save(*args, **kwargs)
        

    def get_short_message(self):
        return u"Slides are late for collection from DTU. "\
               u"The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"Slides from %(dtu)s have not been collected by DTLS for "\
               u"EQA. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline }
               
               
               
class DeliveryToFirstCtrlLate(AlertForBeingLate, CollectedFromDtu):
    """
    State declaring the slides haven't been delivered to first controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+7)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because CollectedFromDtu does and we inherit 
        from it. This is just a reset to prevent recursive calls.
        """
        super(CollectedFromDtu, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides have not been delivered to the first controller. "\
               u"The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"Slides from %(dtu)s have not been delivered to "\
               u"the first controller. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}

class FirstCtrlTestingLate(AlertForBeingLate, 
                                   DeliveredTo1stCtrler):
    """
    State declaring the slides haven't been collected from first controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(weeks=+4)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because DeliveredTo1stCtrler does and we
        inherit from it. This is just a reset to prevent recursive calls.
        """
        super(DeliveredTo1stCtrler, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides are have not been tested by the first controller. "\
               u"The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"Slides from %(dtu)s have still not been tested by the "\
               u"first controller. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}
               
               
     
class FirstCtrlCollectionLate(AlertForBeingLate, 
                                   PassedFirstControl):
    """
    State declaring the slides haven't been collected from first controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(weeks=+1)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because PassedFirstControl does and we
        inherit from it. This is just a reset to prevent recursive calls.
        """
        super(PassedFirstControl, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides have finished first control but have not been "\
               u"collected by the DTLS. The deadline for collection "\
               u"was %s." % self.formated_deadline


    def get_long_message(self):
        return u"Slides from %(dtu)s have finished first control but have "\
               u"not been collected by the DTLS. The deadline was " \
               u"%(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}
               
               
     
class DeliveryToScndCtrlLate(AlertForBeingLate, CollectedFrom1stCtrl):
    """
    State declaring the slides haven't been delivered to second controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(weeks=+2)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because CollectedFrom1stCtrl does and we
          inherit from it. This is just a reset to prevent recursive calls.
        """
        super(CollectedFrom1stCtrl, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides are late for delivery to second controller. "\
               u"The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"Slides from %(dtu)s are late for delivery to second "\
               u" controller. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}

class SecondCtrlTestingLate(AlertForBeingLate, DeliveredTo2ndCtrl):
    """
    State declaring the slides haven't been tested by the second controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(weeks=+4)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because DeliveredTo2ndCtrl does and we
          inherit from it. This is just a reset to prevent recursive calls.
        """
        super(DeliveredTo2ndCtrl, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Slides have not been tested by second controller. "\
               u"The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"Slides from %(dtu)s have not been tested by the second "\
               u" controller. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}

class SecondCtrlReportLate(AlertForBeingLate, ResultsAvailable):
    """
    State declaring report has not been created by the second controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(days=+3)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because ResultsAvailable does and we
          inherit from it. This is just a reset to prevent recursive calls.
        """
        super(ResultsAvailable, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"Preparing of report and preparation of discordant slides "\
               u"is late. The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"The feedback report for %(dtu)s has not been prepared by "\
               u" the second controller. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}

class ReceivedByDtuLate(AlertForBeingLate, ReadyToLeaveNtrl):
    """
    State declaring report has not been created by the second controller
    for too long.
    """

    class Meta:
        app_label = 'findtb'
    
    delay = datetime.timedelta(weeks=+2)
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because ResultsAvailable does and we
          inherit from it. This is just a reset to prevent recursive calls.
        """
        super(ReadyToLeaveNtrl, self).save(*args, **kwargs)


    def get_short_message(self):
        return u"The DTU has not receieved the feedback report and slides. "\
               u"The deadline was %s." % self.formated_deadline


    def get_long_message(self):
        return u"EQA feedback report and slides have not been received by "\
               u" %(dtu)s yet. The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.formated_deadline}
 
 
