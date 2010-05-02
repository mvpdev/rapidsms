#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django_tracking.models import State
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save


class FtbStateManager(models.Manager):


    def get_states(self):
        ct = ContentType.objects.get_for_model(self.model)
        return State.objects.filter(content_type=ct, origin='sref')

    def get_current_states(self):
        return self.get_states().filter(is_current_state=True)

    def get_specimens(self):
        return [state.tracked_item.content_object \
                for state in self.get_current_states()]


class FtbState(models.Model):
    """
    State shared among all states in the FindTB app.
    """

    class Meta:
        app_label = 'findtb'
        abstract = True

    STATE_TYPES = ('notice','result','alert','cancel')
    STATE_ORIGINS = ('findtb','sref','eqa')

    note = models.CharField(max_length=200, null=True, blank=True)
    states = generic.GenericRelation(State)
    state_type = 'notice'
    state_origin = 'findtb'

    objects = FtbStateManager()


    def save(self, *args, **kwargs):

        print "\tFBSTATE: save start"
        print '\t\tself.note: ', self.note
        super(FtbState, self).save(*args, **kwargs)
        # will update the type once the state is save
        post_save.connect(self.set_type, sender=State)
        post_save.connect(self.set_origin, sender=State)
        print "\tFBSTATE: save end"


    def set_type(self, **kwargs):
        """
            Set the type of all states pointing to the current model instance.
            Type is a string that must be one of STATE_TYPES.
        """

        print "\tFBSTATE: set_type start"
        print '\t\tstate_type: ', self.state_type

        if self.state_type not in self.STATE_TYPES:
            raise TypeError("State type must be one of " % \
                            (', '.join(self.STATE_TYPES)))

        print '\t\tGetting states for:', self

        self.states.exclude(type=self.state_type).update(type=self.state_type)

        print "\tFBSTATE: set_type end"


    def set_origin(self, **kwargs):
        """
            Set the origin of all states pointing to the current model instance.
            Type is a string that must be one of STATE_ORIGINS.
        """

        print "\tFBSTATE: set_origin start"
        print '\t\tstate_origin: ', self.state_origin

        if self.state_origin not in self.STATE_ORIGINS:
            raise TypeError("State origin must be one of " % \
                            (', '.join(self.STATE_ORIGINS)))

        print '\t\tGetting states for:', self

        self.states.exclude(origin=self.state_origin)\
                   .update(origin=self.state_origin)

        print "\tFBSTATE: set_origin end"
