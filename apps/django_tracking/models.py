from django.db import models, IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, pre_delete


"""
Track states any Django model, allow to recover history of it's
previous states. State can be any Django model.
"""

# TODO : let the user choose the behaviour for when they delete a state object or a tracked item

def get_generic_relation_holder_for_object(cls, content_object):
    """
    Returns the object pointing to this content object via a generic relationship
    for the class 'cls' if it exists or raise TrackedItem.DoesNotExist.
    Cls must be the class holding the generic relationship and must
    provide a DoesNotExist exception.
    """
    try:
        ct = ContentType.objects.get_for_model(content_object)
        return cls.objects.get(content_type=ct, object_id=content_object.id)
    except ObjectDoesNotExist:
        raise cls.DoesNotExist()


def get_generic_relation_holder_for_object_or_create(cls, content_object,
                                                      *args, **kwargs):
    """
    Returns a tuple containg  the object pointing to this content object
    via a generic relationship if exists or a new object and a boolean
    to specify whether the object has been created or not.
    E.G : (<GenericRelationHolder>, True)
    """

    try:
        return (get_generic_relation_holder_for_object(cls, content_object), False)
    except cls.DoesNotExist:
        return (cls(content_object=content_object, *args, **kwargs), True)


def get_generic_relation_holder_for_objects(cls, content_object):
    """
    Returns a queryset with all the objects pointing to this content object via
    a generic relationship for the class 'cls'.
    """

    ct = ContentType.objects.get_for_model(content_object)

    return cls.objects.filter(content_type=ct, object_id=content_object.id)



class StateError(Exception):
    """
    Exception used when manipulating states. Just a wrapper around Exception
    to allow clean try / catch.
    """
    pass



class State(models.Model):
    """
    A state point to a django object model instance so tracked items can have
    an history of states, which is a collection of any django model declared as
    a state at a given time for a given object.

    This allow you to have a very wide notion of what a state and an history
    is.
    """

    # boiler plate for the generic relation
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    # a simple char to let you filter easily states
    type = models.CharField(max_length=30, blank=True)

    # a cancelled state don't appear in the history, but is not distroyed
    cancelled = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    # The model instance this state belongs to
    tracked_item = models.ForeignKey("TrackedItem", related_name="states")


    # just to allow granular exception catching
    class DoesNotExists(ObjectDoesNotExist, StateError): pass


    class Meta:
        ordering = ['-id']


    def save(self, *args, **kwargs):

        if not hasattr(self, 'tracked_item') or not self.tracked_item.id:
            raise StateError("You cannot save a state without a reference to "\
                             "a saved TrackedItem object. Pass the state to "\
                             "one will let them automatically handle save()"\
                             " for you")

        super(State, self).save(*args, **kwargs)


    def __unicode__(self):

        if not self.created:
            return "Ubound state: %s" % self.content_object

        return "State of at %s of: %s" % (self.created, self.content_object)


    @classmethod
    def on_delete_content_object(cls, sender, *args, **kwargs):
        """
        When the content object is deleted, the state removes itself
        from all the tracked item current state and replace it by None
        then delete itself.
        """
        # TODO : state deletion should happen in a transaction

        for state in cls.get_states_for_object(kwargs['instance']):
            state.tracked_item.state = None
            state.tracked_item.save()
            state.delete()


    @classmethod
    def get_states_for_object(cls, content_object):
        """
        Returns a query set of all the states pointing to that object
        """
        return get_generic_relation_holder_for_objects(cls, content_object)


pre_delete.connect(State.on_delete_content_object, sender=models.Model)



class TrackedItem(models.Model):
    """
    Track the various states a Django model intance has been in.
    A state can any be model and a TrackedItem have an history of all
    the states it has been in, including a current state.
    """

    # boiler plate for the generic relation
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    # the state the model instance is now is
    current_state = models.ForeignKey(State, blank=True, null=True)

    # used to temporarely store a state and save it later to by pass
    # a circular reference
    _state_bak = None


    # just to allow granular exception catching
    class DoesNotExists(ObjectDoesNotExist, StateError): pass


    class Meta: # we don't want a state to be linked to several objects
        unique_together = ('object_id', 'content_type')


    def __unicode__(self):
        return "Traker for %s" % repr(self.content_object)


    def _super_save(self, *args, **kwargs):
        """
        Call the parent model save() with some checks
        """
        try:
            super(TrackedItem, self).save(*args, **kwargs)
        except IntegrityError, e:
            if e.args[0] == 1062: # SQL uniq constraint is not respecte
                raise StateError("The model instance %s is already tracked"\
                             % unicode(self))


    def save(self, *args, **kwargs):
        """
        Overloaded save() so we can add a state even with the circular
        reference between a state and a tracked item.
        """

        # If _state_bak is full, then it means that is TrackedItem is
        # newly created and not saved yet. Deal with cirlar reference with
        # the state object.
        if self._state_bak:
            # we need a id to save a new state
            self._super_save(*args, **kwargs)
            self.current_state = self._state_bak
            self._state_bak = None

        # Saving the state automatically now
        # You can't save a state manually outside a non saved Tracked Item.
        if self.state :
            self.state.tracked_item = self
            self.state.save()

        self._super_save(*args, **kwargs)


    def get_history(self):
        """
        Returns the queryset of the states this tracked object has been in.
        """

        return self.states.filter(cancelled=False)


    def get_previous_state(self):
        """
        Give you the previous state in the history of this tracked object.
        """
        previous_states = self.get_history().filter(id__lt=self.state.id)
        if previous_states.count():
            return previous_states[0]

        return None


    def set_to_next_state(self, next_state):
        """
        Set the tracked object to it's next state.
        """

        if next_state is None:
            self.current_state = None

        else:
            # For now, we allow only Django model to be states
            if not isinstance(next_state, models.Model):
                # TODO : allow any object using serialisation
                raise StateError("A state must be a django model or None")

            # The next state must be a state object
            # TODO : use duck typing for state object
            if not isinstance(next_state, State):
                next_state = State(content_object=next_state)

            # Prevent two track item to share a state object
            # Several state objects can point to the same
            # models instance, however
            if next_state.id and next_state.tracked_item.id != self.id:
                raise StateError("This state is already used by another tracked item")

            # if no id, it's a new TrackedItem and you use the _state_bak trick
            if not self.id:
                self._state_bak = next_state
            else:
                self.current_state = next_state


    def cancel_current_state(self):
        """
        Cancel the current state and go back to the previous one.
        Can't work if there is only one state.
        """

        if not self.state.id :
            raise StateError("Current state should be saved before cancelling")

        if not self.id :
            raise StateError("Unable to cancel a state on a unsaved tracked item")

        if self.state:

            if not self.state.created:
                raise StateError("Can't cancel un unsave state: "\
                                 "save the TrackedItem if you want "\
                                 "to cancel a state you just added")

            self.state.cancelled = True
            self.state.save()

        self.state = self.get_previous_state()


    state = property((lambda s: s.current_state or s._state_bak),
                     set_to_next_state,
                     cancel_current_state,
                     "The current state this tracked object is in. "\
                     "All states are saved in an history. "\
                     "A state can any Django model" )


    # TODO : add a way to untrack event

    @classmethod
    def get_tracker_for_object(cls, content_object):
        """
        Returns the TrackedItem object pointing to this content object if
        it exists or raise TrackedItem.DoesNotExist.
        """
        return get_generic_relation_holder_for_object(cls, content_object)


    @classmethod
    def get_tracker_for_object_or_create(cls, content_object):
        """
        Returns a tuple containg a TrackedItem object pointing to this content
        object if exists or a new TrackedObject and a boolean to specify
        whether the object has been created or not.
        E.G : (<TrackedItem>, True)
        """

        return get_generic_relation_holder_for_object_or_create(cls, content_object)


    @classmethod
    def on_delete_content_object(cls, sender, *args, **kwargs):

        try:
            ti = cls.get_tracker_for_object(kwargs['instance'])
        except cls.DoesNotExist:
            return None

        # TODO : make the delete happen in a transaction
        ti.states.all().delete()
        ti.delete()

    # TODO : add signals for incomming event, cancelling event, outgoing from events, etc
    # TODO : add an event "on one of my state deleted"
    # TODO : make a registration so any registered model get tracked



post_delete.connect(TrackedItem.on_delete_content_object, sender=models.Model)
