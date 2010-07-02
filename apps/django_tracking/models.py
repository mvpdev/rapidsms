from django.db import models, IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
#from django.db.models.signals import post_delete, pre_delete

"""
Track states of any Django model, allow to recover history of it's
previous states. State can and must be any Django model.
"""

# TODO : let the user choose the behaviour for when they delete a state object or a tracked item

def get_generic_relation_holder(cls, content_object):
    """
    Returns the object pointing to this content object via a generic relationship
    for the class 'cls' if it exists or raise TrackedItem.DoesNotExist.
    Cls must be the class holding the generic relationship and must
    provide a DoesNotExist exception.
    """

    try:
        ct = ContentType.objects.get_for_model(content_object)
        return cls.objects.get(content_type=ct, object_id=content_object.pk)
    except ObjectDoesNotExist, AttributeError:
        raise cls.DoesNotExist()


def get_generic_relation_holder_or_create(cls, content_object,
                                                      *args, **kwargs):
    """
    Returns a tuple containg  the object pointing to this content object
    via a generic relationship if exists or a new object and a boolean
    to specify whether the object has been created or not.
    E.G : (<GenericRelationHolder>, True)
    """

    try:
        return (get_generic_relation_holder(cls, content_object), False)
    except cls.DoesNotExist:
        return (cls(content_object=content_object, *args, **kwargs), True)


def get_generic_relation_holders(cls, content_object):
    """
    Returns a queryset with all the objects pointing to this content object via
    a generic relationship for the class 'cls'.
    """

    ct = ContentType.objects.get_for_model(content_object)
    return cls.objects.filter(content_type=ct, object_id=content_object.pk)



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

    # allow filtering state by a type, whatever it means
    type = models.CharField(max_length=30, blank=True)

    # allow filtering state by a title, whatever it means
    title = models.CharField(max_length=60, blank=True)

    # allow filtering state by origin, whatever it means
    origin = models.CharField(max_length=30, blank=True)

    # a cancelled state don't appear in the history, but is not distroyed
    cancelled = models.BooleanField(default=False)

    # if there is not state after this one
    is_final = models.BooleanField(default=False)

    # if this state is currently the current state for any tracked item
    is_current = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    # The model instance this state belongs to
    tracked_item = models.ForeignKey("TrackedItem", related_name="states")


    # just to allow granular exception catching
    class DoesNotExists(ObjectDoesNotExist, StateError): pass


    class Meta:
        ordering = ['-id']

    # TODO : think about what to do with this double saving

    def __init__(self, *args, **kwargs):
        co = kwargs.get('content_object', None)
        if co:
            co.save()
        super(State, self).__init__(*args, **kwargs)


    def save(self, *args, **kwargs):
        if self.content_object:
            self.content_object.save()
        super(State, self).save(*args, **kwargs)


    def __unicode__(self):

        if not self.created:
            return "Ubound state: %s" % self.content_object

        return "State of at %s of: %s" % (self.created, self.content_object)


    @classmethod
    def on_delete_content_object(cls, sender, **kwargs):
        """
        When the content object is deleted, the state removes itself
        from all the tracked item current state and replace it by None
        then delete itself.
        """
        # TODO : state deletion should happen in a transaction

        for state in cls.get_states(kwargs['instance']):

            state.tracked_item.state = None
            state.tracked_item.save()
            state.delete()



    @classmethod
    def get_states(cls, content_object):
        """
        Returns a query set of all the states pointing to that object
        """
        return get_generic_relation_holders(cls, content_object)


#pre_delete.connect(State.on_delete_content_object,)



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

    # the state the model instance is now in
    current_state = None


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
                raise StateError("This model instance (%s) is already tracked"\
                                 % unicode(self))


    def save(self, *args, **kwargs):
        """
        Overloaded save() so we can add a state and the its metadata.
        """

        self._super_save(*args, **kwargs)

        # Saving the state automatically now
        # You can't save a state manually outside a non saved Tracked Item.

        if self.state :
            self.state.tracked_item = self
            self.state.is_current = True
            self.state.save()

        # mark the previous state as not being the current one anymore
        previous_state = self.get_previous_state()
        if previous_state:
            previous_state.is_current = False
            previous_state.save()


    def get_history(self):
        """
        Returns the queryset of the states this tracked object has been in.
        """

        return self.states.filter(cancelled=False)


    def get_previous_state(self):
        """
        Give you the previous state in the history of this tracked object.
        Returns None s there is no previous state.
        """
        try:
            return self.get_history().filter(pk__lt=self.state.pk)[0]
        except (IndexError, AttributeError): # no previous or current state
            return None


    def set_to_next_state(self, next_state):
        """
        Set the tracked object to it's next state. If you set it to None,
        only the local object is affected.
        """

        if next_state is not None:

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
            if next_state.pk and next_state.tracked_item.pk != self.pk:
                raise StateError("This state is already used by another tracked item")

            next_state.tracked_item = self

        self.current_state = next_state


    def cancel_current_state(self):
        """
        Cancel the current state and go back to the previous one.
        Can't work if there is only one state.
        """

        if not self.pk :
            raise StateError("Cannot cancel a state of a unsaved tracked item")

        if self.state:

            if not self.state.pk :
                raise StateError("Cannot cancel an unsaved state")

            self.state.cancelled = True
            self.state.save()

        self.state = self.get_previous_state()


    def get_current_state(self):
        """
        Returns the most recent of the non conceled states in history.
        """

        if not self.current_state:

            try :
                self.current_state = self.get_history()[0]
            except IndexError:
                return None

        return self.current_state


    state = property(get_current_state,
                     set_to_next_state,
                     cancel_current_state,
                     "The current state this tracked object is in. "\
                     "All states are saved in an history. "\
                     "A state can be any and only Django models" )


    # TODO : add a way to untrack event

    @classmethod
    def get_tracker(cls, content_object):
        """
        Returns the TrackedItem object pointing to this content object if
        it exists or raise TrackedItem.DoesNotExist.
        """

        return get_generic_relation_holder(cls, content_object)


    @classmethod
    def get_tracker_or_create(cls, content_object):
        """
        Returns a tuple containg a TrackedItem object pointing to this content
        object if exists or a new TrackedObject and a boolean to specify
        whether the object has been created or not.
        E.G : (<TrackedItem>, True)
        """

        return get_generic_relation_holder_or_create(cls, content_object)


    @classmethod
    def on_delete_content_object(cls, sender, **kwargs):

        try:
            ti = cls.get_tracker(kwargs['instance'])
        except cls.DoesNotExist:
            return None

        # TODO : make the delete happen in a transaction
        ti.states.all().delete()
        ti.delete()


    @classmethod
    def add_state_to_item(cls, content_object, state):
        """
            Get or create the tracker, save the state, add it then
            save the tracker in one row.
        """

        ti, created = cls.get_tracker_or_create(content_object)
        ti.state = state
        ti.save()

        return (ti, ti.state)



    # TODO : add signals for incomming event, cancelling event, outgoing from events, etc
    # TODO : add an event "on one of my state deleted"
    # TODO : make a registration so any registered model get tracked



#post_delete.connect(TrackedItem.on_delete_content_object)
