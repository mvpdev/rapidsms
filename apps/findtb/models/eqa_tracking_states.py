#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

"""
Models collection to manage EQA system statuses and results.
All models rely on the django_tracking application.
"""

from dateutil.relativedelta import relativedelta

from django.db import models

from celery.registry import tasks
from celery.decorators import task

from django_tracking.models import TrackedItem

from models import SlidesBatch
from ftbstate import FtbState


class Eqa(FtbState):
    """
    Common parent extended by all models in EQA
    """
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
    def eqa_dtu_collection_reminder(self):
        """
        Check if EQA is late, and if yes trigger and alerts.
        """
        print "in reminder"
        try:
            sb = SlidesBatch.objects.get(pk=self.slides_batch.pk)
        except SlidesBatch.DoesNotExist:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=sb)
            if ti.state.title == u'eqa_starts' and ti.state.type != 'alert':
                state = DtuCollectionIsLate(slides_batch=sb)
                state.save()
                ti.state = state
                ti.save()
                msg = state.get_long_message()
                from findtb.libs.utils import send_to_ztls, send_to_dtu_focal_person, send_to_dtls
                send_to_dtu_focal_person(sb.location, msg)
                send_to_dtls(sb.location, msg)
                send_to_ztls(sb.location, msg)
    tasks.register(eqa_dtu_collection_reminder)


    def save(self, *args, **kwargs):
        """
        Setup the alert.
        """

        if not self.pk:
            in_one_week = self.slides_batch.created_on + relativedelta(weeks=+1)
            self.eqa_dtu_collection_reminder.apply_async(eta=in_one_week,
                                                              args=(self,))
        
        super(EqaStarts, self).save(*args, **kwargs)



    def get_short_message(self):

        return u"Slides are ready to be picked up by DTLS"


    def get_long_message(self):

        return u"Slides from %(dtu)s are ready to be picked up by the DTLS" % {
                                            'dtu': self.slides_batch.location }


class CollectedFromDtu(Eqa):
    """
    State declaring the slides have been collected by DTLS from the
    DTU.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'collected_from_dtu'


    def get_short_message(self):

        return u"%s slides have been collected by the DTLS from the DTU." %\
               self.slides_batch.slide_set.all().count()


    def get_long_message(self):

        return u"%(number)s slides have been picked up from %(dtu)s by the DTLS" % {
                                            'dtu': self.slides_batch.location.name,
                                            'number': self.slides_batch.slide_set.all().count()}


class DeliveredToFirstController(Eqa):
    """
    State declaring the slides have been delivered by DTLS to the first
    controller.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'delivered_to_first_controller'


    def get_short_message(self):

        return u"Slides have been delivered to the first controller"


    def get_long_message(self):

        return u"Slides from %(dtu)s have been delivered to the first controller" % {
                                            'dtu': self.slides_batch.location.name}



class PassedFirstControl(Eqa):
    """
    State declaring the slides have been tested by the first
    controller.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'passed_first_control'


    def get_short_message(self):

        return u"Slides have been tested by the first controller"


    def get_long_message(self):

        return u"Slides from %(dtu)s have been tested by the first controller" % {
                                            'dtu': self.slides_batch.location.name}


class CollectedFromFirstController(Eqa):
    """
    State declaring the slides have been collected by DTLS from the
    first controller.
    """

    class Meta:
        app_label = 'findtb'
        
    state_type = 'alert'

    state_name = 'collected_from_first_controller'


    def get_short_message(self):

        return u"Slides have been picked up by the DTLS"


    def get_long_message(self):

        return u"Slides from %(dtu)s have been picked up from the first controller by the DTLS" % {
                'dtu': self.slides_batch.location.name}


class DeliveredToSecondController(Eqa):
    """
    State declaring the slides have been delivered by DTLS to the second
    controller.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'delivered_to_second_controller'


    def get_short_message(self):

        return u"Slides have been delivered to the second controller"


    def get_long_message(self):

        return u"Slides from %(dtu)s have been delivered to the second controller" % {
                                            'dtu': self.slides_batch.location.name}


class ResultsAvailable(Eqa):
    """
    State declaring the results for the slides are available.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'results_available'
    state_type = 'result'


    def get_short_message(self):

        return u"EQA results: %s" % self.slides_batch.results


    def get_long_message(self):

        return u"EQA results for slides from %(dtu)s: %(results)s" % {
                'dtu': self.slides_batch.location.name,
                'results': self.slides_batch.results }
                
                
class ReadyToLeaveNtrl(Eqa):
    """
    State declaring the slides are ready to leave NTRL.
    """

    class Meta:
        app_label = 'findtb'

    state_name = 'ready_to_leave_ntrl'


    def get_short_message(self):

        return u"Slides are ready to be sent back to DTU"


    def get_long_message(self):

        return u"Slides from %(dtu)s are ready to be sent back to DTU" % {
                'dtu': self.slides_batch.location.name}


class ReceivedAtDtu(Eqa):
    """
    State declaring have been received at DTU.
    """

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
                
         
         
class DtuCollectionIsLate(EqaStarts):
    """
    State declaring the slides haven't been picked up from DTU for too long.
    """

    class Meta:
        app_label = 'findtb'
        
    state_type = 'alert'
    
    
    def save(self, *args, **kwargs):
        """
        We must override it because EqaStarts does and we inherit from it.
        This is just a reset.
        """
        super(EqaStarts, self).save(*args, **kwargs)
        
        
    def get_deadline(self):
        return self.slides_batch.created_on + relativedelta(weeks=+1)


    def get_short_message(self):

        return u"Slides are late for collection from DTU. "\
               u"The deadline was %s." % self.get_deadline()


    def get_long_message(self):

        return u"Slides from %(dtu)s are late for collection from DTU. "\
               u"The deadline was %(deadline)s." % {
               'dtu': self.slides_batch.location,
               'deadline': self.get_deadline() }
