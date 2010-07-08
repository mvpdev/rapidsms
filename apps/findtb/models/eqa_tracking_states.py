#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

"""
Models collection to manage Specimen Referral system statuses and results.
All models rely on the django_tracking application.
"""

from django.db import models

from findtb.models.models import SlidesBatch
from findtb.models.ftbstate import FtbState

class Eqa(FtbState):
    """
    Common parent extended by all models in EQA
    """
    class Meta:
        app_label = 'findtb'

    slides_batch = models.ForeignKey(SlidesBatch)
    state_origin = 'eqa'

    STATE_NAMES = ('eqa_starts')

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

        return u"%s slides have been picked up by the DTLS" %\
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