from django.db import models, IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.core.signals import post_delete

"""
Track states any Django model, allow to recover history of it's
previous states. State can be any Django model.
"""


def get_content_type(content_object):
    """
        Get the content_type of a content_object if it exists or raise
        exception.
    """

    app = content_object.__module__.split(".")[0]
    model = content_object.__class__.__name__

    return ContentType.objects.get(app_label=app, model=model)




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
    cancelled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    tracked_item = models.ForeignKey("TrackedItem", related_name="states")

    # TODO : add some management for when they delete a state object or a tracked item
    # TODO : let the user choose the behaviour for that
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



class TrackedItem(models.Model):
    """
    Generic model you can use to track the various states
    another model has been.
    A state can any be model.
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    current_state = models.ForeignKey(State, blank=True, null=True)

    _state_bak = None

    class DoesNotExists(ObjectDoesNotExist, StateError): pass

    class Meta: # we don't want a state to be linked to several objects
        unique_together = ('object_id', 'content_type')


    def __unicode__(self):
        return "Traker for %s" % repr(self.content_object)


    def _super_save(self, *args, **kwargs):
        """
        Call the parent model "save" method with some checks
        """
        print "Saving parent"
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

        return self.states.filter(cancelled=False)


    def get_previous_state(self):
        """
        Give you the previous state in the history of the tracked object.
        """
        previous_states = self.get_history().filter(id__lt=self.state.id)
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

            if next_state.id and next_state.tracked_item.id != self.id:
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


    def cancel_current_state(self):
        """
        Cancel the current state and go back to the previous one.
        Can't work if there is only one state.
        """
        # TODO : raise error if states no saved

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
    # TODO : is tracked classmethod

    @classmethod
    def get_tracker(cls, content_object):
        """
        Returns the TrackedItem object pointing to this content object if
        it exists or raise TrackedItem.DoesNotExist.
        """

        ct = get_content_type(content_object)
        try:
            return TrackedItem.objects.get(content_type=ct,
                                       object_id=content_object.id)
        except ObjectDoesNotExist:
            raise TrackedItem.DoesNotExist()


    @classmethod
    def get_tracker_or_create(cls, content_object):
        """
        Returns a tuple containg a TrackedItem object pointing to this content
        object if exists or a new TrackedObject and a boolean to specify
        whether the object has been created or not.
        E.G : (<TrackedItem>, True)
        """

        ct = get_content_type(content_object)
        try:
            return (TrackedItem.objects.get(content_type=ct,
                                       object_id=content_object.id), False)
        except ObjectDoesNotExist:
            return (TrackedItem(content_object=content_object), True)


    @classmethod
    def on_delete_content_object(sender, **kwargs):

        try:
            ti = TrackedItem.get_tracker(kwargs['instance'])
        except TrakedItem.DoesNotExist:
            return None
        # TODO : make the delete happen in a transaction
        ti.states.all().delete()
        ti.delete()



post_delete.connect(TrackedItem.on_delete_content_object)


    # TODO : make a registration so any registered model get tracked

# Have to do that since I can't figure how to make rapid sms unit test work
def test():

    from locations.models import Location
    from django.contrib.auth.models import Permission

    l = Location.objects.all();
    p = Permission.objects.all();

    print "You can save a TrackedItem twice in a row"
    t1 = TrackedItem(content_object=l[0])
    t1.save()
    t1.save()

    print "Default state is None"
    assert t1.state is None

    print "You have access to the underlying model"
    assert t1.content_object.name == l[0].name

    print "You can add a django model as a state after the state has been saved once"
    t1.state = l[0]
    t1.save()
    s1 = t1.state

    print "Any django model can be added as a state"
    t1.state = p[0]
    t1.save()
    s2 = t1.state

    print "You can add a model, then change you mind and add a new one then change"
    t1.state = p[0]
    t1.state = l[0]
    t1.save()
    s3 = t1.state

    print "You can access the history of all the previous state in chronological order"
    hist = list(t1.get_history())
    assert s1 == hist[-1]
    assert s2 == hist[-2]
    assert s3 == hist[-3]

    print "The first state in history is the current state"
    assert t1.state == hist[0]

    print "You can't track the same item twice: it raises a StateError"
    try:
        t2 = TrackedItem(content_object=l[0])
        t2.save()
        assert False
    except StateError:
        pass

    print "You can add a state to a not saved tracked item then save it"
    t2 = TrackedItem(content_object=l[1])
    t2.save()

    print "Two distinct histories don't overlap."
    t2.state = l[1]
    t2.save()

    assert not set(t2.get_history()).intersection(set(t1.get_history()))


    print "You can cancel a state by using 'del',"\
          " it makes you going back to the previous state"
    s = t1.state
    del t1.state
    t1.save()
    assert t1.state == s2

    print "The cancelled state is not destroyed, it's just set to cancelled"
    assert t1.states.all()[0] == s
    assert t1.states.all()[0].cancelled

    print "You can add a new state after the cancelled state, and it will appear after"
    t1.state = p[0]
    t1.save()
    assert t1.states.all()[0] == t1.state
    assert t1.states.all()[1] == s

    print "The cancelled state does not appear in the history"
    states = t1.get_history()
    assert states[1] != s

    print "A single model instance can a state for several tracked item"
    t2.state = p[0]
    t2.save()

    print "You can add a model object which is already wrapped in a State"
    s = State(content_object=l[0])
    t2.state = s
    t2.save()

    print "You can't save states outside a TrackedItem. It raises a StateError"
    s = State(content_object=l[5])
    try:
        s.save()
        assert False
    except StateError, e:
        pass

    print "You can access to the underlying model behind a State"
    assert isinstance(s.content_object.name, unicode)

    print "You can retrieve any the content type of an object from an object"
    print t1.content_type
    print get_content_type(t1.content_object)
    assert t1.content_type == get_content_type(t1.content_object)

    print "You can get a TrackedItem from the model"
    t3 = TrackedItem.get_tracker(content_object=t1.content_object)
    print t1, t1.id, t1.content_object, t1.content_object.id
    print t3, t3.id, t3.content_object, t3.content_object.id
    assert t1 == t3

    print "If the model doesn't exists, it raises a TrackedItem.DoesNotExists exception"
    try:
        t4 = TrackedItem.get_tracker(content_object=l[10])
        assert False
    except TrackedItem.DoesNotExist:
        pass

    print "You can get a tracked Item from the model or a new model if it does no exist"
    print "A tuple will contain the object and a boolean say if it has been created"
    t3 = TrackedItem.get_tracker_or_create(content_object=t1.content_object)
    t4 = TrackedItem.get_tracker_or_create(content_object=l[10])

    assert t1 == t3[0]
    assert not t3[1]
    assert isinstance(t4[0], TrackedItem)
    assert t4[1]

    print "Deleting a content object will delete the associated item and states"
    print "A non tracked object deletion should no trigger anything"
    t5 = TrackedItem.get_tracker_or_create(content_object=l[11])[0]
    t5.state = p[0]
    t5.save()
    t5.state = p[1]
    t5.save()
    l[11].delete()

    try:
        TrackedItem.objects.get(id=t5.id)
        assert False
    except Exception, e:
        print e
