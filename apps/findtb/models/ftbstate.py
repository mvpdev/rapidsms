#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django_tracking.models import State
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType



class FtbStateManager(models.Manager):
    def get_current_states(self):
        ct = ContentType.objects.get_for_model(self.model)
        return State.objects.filter(content_type=ct, is_current_state=True)


class FtbState(models.Model):
    """
    State shared among all states in the FindTB app.
    """
    
    class Meta:
        app_label = 'findtb'
        abstract = True

    STATE_TYPES = ('notice','result','alert','cancel')


    note = models.CharField(max_length=200, null=True, blank=True)
    states = generic.GenericRelation(State)
    state_type = 'notice'
    
    objects = FtbStateManager()


    def save(self, *args, **kwargs):

        print "\tFBSTATE: save start"
        print '\t\tself.note: ', self.note
        super(FtbState, self).save(*args, **kwargs)
        self.set_type(self.state_type)
        print "\tFBSTATE: save end"


    def set_type(self, state_type):
        """
            Set the type of all states pointing to the current model instance.
            Type is a string that must be one of STATE_TYPES.
        """

        print "\tFBSTATE: set_type start"
        print '\t\tstate_type: ', state_type

        if state_type not in self.STATE_TYPES:
            raise TypeError("State must be one of " % \
                            (', '.join(self.STATE_TYPES)))

        for state in State.get_states_for_object(self):
            state.type = state_type

        print "\tFBSTATE: set_type end"
