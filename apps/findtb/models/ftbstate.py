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
        return self.get_states().filter(is_current=True)


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

    STATE_TYPES = ('notice','result','alert','cancelled')
    STATE_ORIGINS = ('findtb','sref','eqa')

    note = models.CharField(max_length=200, null=True, blank=True)
    states = generic.GenericRelation(State)
    state_type = 'notice'
    state_origin = 'findtb'
    state_name = 'findtb'
    next_state_name = ''

    objects = FtbStateManager()


    def save(self, *args, **kwargs):

        print "\tFBSTATE: save start"
        print '\t\tself.note: ', self.note
        super(FtbState, self).save(*args, **kwargs)
        # will update the type once the state is save
        post_save.connect(self.update_upper_state, sender=State)
        print "\tFBSTATE: save end"


    def update_upper_state(self, sender, **kwars):
        """
            Batching update of the upper state after it get saved.
            We do that using signals because when this object is saved,
            the state is not yet.
        """
        self.set_type(**kwars)
        self.set_origin( **kwars)
        self.set_name( **kwars)
        self.set_is_final(is_final=bool(self.get_next_state_class()),
                          **kwars)


    # TODO: make these functions working without a side effect.
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


    def set_is_final(self, **kwargs):
        """
            Set is_final for all states pointing to the current model instance.
            Type is a bool.
        """

        print "\tFBSTATE: set_origin start"
        is_final = kwargs.get('is_final', False)
        print '\t\tfinal: ', is_final

        print '\t\tGetting states for:', self

        self.states.exclude(is_final=is_final)\
                   .update(is_final=is_final)

        print "\tFBSTATE: set_is_final end"


    def set_name(self, **kwargs):
        """
            Set the name of all states pointing to the current model instance.
            Type is a string that must be one of STATE_NAMES.
        """

        print "\tFBSTATE: set_name start"
        print '\t\tstate_name: ', self.state_name

        #TODO : look at that later

#        if self.state_name not in self.STATE_NAMES:
#            raise TypeError("State name must be one of " % \
#                            (', '.join(self.STATE_NAMES)))

        print '\t\tGetting states for:', self

        self.states.exclude(title=self.state_name)\
                   .update(title=self.state_name)

        print "\tFBSTATE: set_name end"


    def get_next_state_class(self, **kwargs):
        """
            Return the class of the next state after this one.
            If none, the this state is a final.
        """

        None
