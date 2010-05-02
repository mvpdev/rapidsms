#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django_tracking.models import State
from django.contrib.contenttypes import generic

class FtbState(models.Model):
    """
    State shared among all states in the FindTB app.
    """
    
    class Meta:
        app_label = 'findtb'

    STATE_TYPES = ('notice','result','alert','cancel')


    note = models.CharField(max_length=200, null=True, blank=True)
    states = generic.GenericRelation(State)
    state_type = 'notice' 

    def __init__(self, note, *args, **kwargs):

        print "\tFBSTATE: __init__ start"
        print '\t\tnote: ', note
        print '\t\targs:', args
        print '\t\tkwargs:', kwargs

        models.Model.__init__(self, *args, **kwargs)

        self.note = note

        print "\tFBSTATE: __init__ end"


    def save(self, *args, **kwargs):

        print "\tFBSTATE: save start"
        print '\t\tself.note: ', self.note

        models.Model.save(self, *args, **kwargs)
        #super(FtbState, self).save(*args, **kwargs)
               
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
    
