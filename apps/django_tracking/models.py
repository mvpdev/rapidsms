from django.db import models, IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from operator import attrgetter

"""
Contains all the virtual class to use when you want to track a model.
"""


class StateError(Exception):
    """
    Exception used when manipulating states. Just a wrapper around Exception
    to allow clean try / catch.
    """
    pass



class State(models.Model):
    """
    A state in which any tracked object can be. Virtual, should be subclassed.

    """

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    type = models.CharField(max_length=30, blank=True)
    cancel = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    tracked_item = models.ForeignKey("TrackedItem", related_name="states_set")


    class Meta: # we don't want a state to be linked to several objects
        ordering = ['-created']


    def __unicode__(self):

        if not self.created:
            return "Ubound state: %s" % self.content_object

        return "State of at %s of: %s" % (self.created, self.content_object)


class TrackedItem(models.Model):
    """
    Generic model you can use to track the various states
    another model has been.
    A state can any model
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    current_state = models.ForeignKey(State, blank=True, null=True)

    _state_bak = None

    def __unicode__(self):
        return "Traker for %s" % repr(self.content_object)


    def _super_save(self, *args, **kwargs):
        """
        Call the parent model "save" method with some checks
        """
        print "Saving parent"
        try:
            super(TrackedItem, self).save(self, *args, **kwargs)
        except IntegrityError, e:
            raise e
            if e.args[0] == 1062: # SQL uniq constraint is not respecte
                raise StateError("The model instance %s is already tracked"\
                             % unicode(self))
            else:
                raise e


    def save(self, *args, **kwargs):
        """
        Overloaded save() so we can add a state even with the circular
        reference between a state and a tracked item.
        """
        print "Saving tracker"
        if self._state_bak:
            # we need a id to save a new state
            # if a new state is added, create the tracked item
            # without state first
            print "Temp var contain a state."
            self._super_save(*args, **kwargs)
            print "Setting the current state from the temp var"
            self.current_state = self._state_bak
            self._state_bak = None
            print "Current state is %s" % self.state
            print "Temp var is %s" % self._state_bak


        if self.state :
            print "State is not None Saving."
            self.state.tracked_item = self
            self.state.save()

        self._super_save(*args, **kwargs)
        print "Saving tracker done !"


    def get_history(self):
        """
        Get the queryset of the states this tracked object has been in.
        """

        return self.states_set.filter(cancel=False)


    def get_previous_state(self):
        """
        Give you the previous state in the history of the tracked object.
        """
        previous_states = self.get_history().filter(created_lt=self.state.created)
        if previous_states.count():
            return previous_states[0]

        return None


    def set_to_next_state(self, next_state):
        """
        Set the tracked object to it's next state.
        """
        print "Setting new state %s" % next_state
        if next_state is None:
            print "State is None"
            self.current_state = None

        else:
            print "State is not None"
            if not isinstance(next_state, models.Model):
                # TODO : allow any object using serialisation
                raise StateError("A state must be a django model or None")
            print "State is a django model"

            if not isinstance(next_state, State):
                print "Passed state is not a state object. Wrapping it"
                next_state = State(content_object=next_state)
                print "State is now %s" % next_state

            if next_state.created:
                raise StateError("This state is already used by another tracked item")

            print "The state is a new one"

            if not self.id:
                print "This tracker is not saved : put state in temp var"
                self._state_bak = next_state
                print "Temp var is now : %s" % self._state_bak
            else:
                print "This tracker is already saved : put state in current_state"
                self.current_state = next_state

                print "Current state is : %s" % self.state


    def cancel(self):
        """
        Cancel the current state and go back to the previous one.
        Can't work if there is only one state.
        """
        # TODO : raise error if states no saved

        if self.state:

            if not self.state.created:
                raise StateError("Can't cancel un unsave state."\
                                 "Save the TrackedItem if you want "\
                                 "to cancel a state you just added.")

            self.state.cancel = True

        self.state = self.get_previous_state()


    state = property((lambda s: s.current_state or s._state_bak),
                     set_to_next_state,
                     cancel,
                     "The current state this tracked object is in. "\
                     "All states are saved in an history. "\
                     "A state can any Django model" )

