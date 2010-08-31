#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.db import models
from django_tracking.models import State
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save


class FtbStateManager(models.Manager):
    def get_states(self, include_siblings=False):
        """
        Get all the states related to this model
        
        include_siblings add states with the same title but not the same
        content type
        """
        states = State.objects.filter(title=self.model.state_name,
                                      origin=self.model.state_origin)
        if not include_siblings:
            ct = ContentType.objects.get_for_model(self.model)
            states = states.filter(content_type=ct)
        return states


    def get_current_states(self, include_siblings=False):
        """
        Get all the states related to this model, that are current states.
        """
        return self.get_states(include_siblings).filter(is_current=True)


    def get_specimens(self, include_siblings=False):
        """
        Get all the specimens that are in this state
        """
        return [state.tracked_item.content_object \
                for state in self.get_current_states(include_siblings)]


class FtbState(models.Model):
    """
    State shared among all states in the FindTB app.
    """

    class Meta:
        app_label = 'findtb'
        abstract = True

    STATE_TYPES = ('notice','result','alert','cancelled', 'checked')
    STATE_ORIGINS = ('findtb','sref','eqa')

    note = models.CharField(max_length=200, null=True, blank=True)
    states = generic.GenericRelation(State)
    state_type = 'notice'
    state_origin = 'findtb'
    state_name = 'findtb'
    next_state_name = ''

    objects = FtbStateManager()


    def save(self, *args, **kwargs):

        super(FtbState, self).save(*args, **kwargs)
        # will update the type once the state is save
        post_save.connect(self.update_upper_state, sender=State)


    def update_upper_state(self, sender, **kwars):
        """
            Batching update of the upper state after it get saved.
            We do that using signals because when this object is saved,
            the state is not yet.
        """
        self.set_type(**kwars)
        self.set_origin( **kwars)
        self.set_name( **kwars)
        self.set_is_final(**kwars)


    # TODO: make these functions working without a side effect.
    def set_type(self, **kwargs):
        """
            Set the type of all states pointing to the current model instance.
            Type is a string that must be one of STATE_TYPES.
        """
        if self.state_type not in self.STATE_TYPES:
            raise TypeError('State type must be one of: "%s"' % \
                            ('", "'.join(self.STATE_TYPES)))

        self.states.exclude(type=self.state_type).update(type=self.state_type)


    def set_origin(self, **kwargs):
        """
            Set the origin of all states pointing to the current model instance.
            Type is a string that must be one of STATE_ORIGINS.
        """

        if self.state_origin not in self.STATE_ORIGINS:
            raise TypeError("State origin must be one of " % \
                            (', '.join(self.STATE_ORIGINS)))


        self.states.exclude(origin=self.state_origin)\
                   .update(origin=self.state_origin)


    def set_is_final(self, **kwargs):
        """
            Set is_final for all states pointing to the current model instance.
            Type is a bool.
        """

        is_final = kwargs.get('is_final',
                               False) or getattr(self, 'is_final', False)
        self.states.exclude(is_final=is_final)\
                   .update(is_final=is_final)


    def set_name(self, **kwargs):
        """
            Set the name of all states pointing to the current model instance.
            Type is a string that must be one of STATE_NAMES.
        """


        #TODO : look at that later

#        if self.state_name not in self.STATE_NAMES:
#            raise TypeError("State name must be one of " % \
#                            (', '.join(self.STATE_NAMES)))

        self.states.exclude(title=self.state_name)\
                   .update(title=self.state_name)


