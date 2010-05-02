#!/usr/bin/env python
# -*- coding= UTF-8 -*-

__author__  = 'ksamuel <ksamuel@gmail.com>'

from locations.models import Location
from django.contrib.auth.models import Permission
from models import *

# Have to do that since I can't figure how to make rapid sms unit test work
# Don't cry, I'd like to be able to use the unittest module too

def test():

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

    print "You can't cancel a state if the current state is not saved"
    print "It raises a StateError"
    t1.state = p[22]
    try:
        del t1.state
        assert False
    except StateError:
        pass

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
    print ContentType.objects.get_for_model(t1.content_object)
    assert t1.content_type == ContentType.objects.get_for_model(t1.content_object)

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

    print "You can delete a non tracked item without any consequence"
    p[33].delete()

    print "Deleting a content object will delete the associated item and states"
    t5, created = TrackedItem.get_tracker_or_create(content_object=p[11])
    t5.state = p[0]
    t5.save()
    t5.state = p[1]
    t5.save()

    assert State.objects.filter(tracked_item=t5.id).count() == 2

    try:
        t7 = TrackedItem.objects.get(id=t5.id)
        assert True
    except Exception, e:
        assert True


    t7.states.all().count() == 2

    p[11].delete()

    try:
        TrackedItem.objects.get(id=t5.id)
        assert False
    except Exception, e:
        pass
    print State.objects.filter(tracked_item=t5.id).count()
    assert State.objects.filter(tracked_item=t5.id).count() == 0

    print "Deleting a content object linked to a state delete the state"
    t8, created = TrackedItem.get_tracker_or_create(content_object=l[29])
    assert created

    t8.state = p[2]
    t8.save()
    s = t8.state
    t8.state = p[3]
    t8.save()

    assert t8.states.all().count() == 2

    s.content_object.delete()

    assert t8.states.all().count() == 1

    assert list(t8.states.all()).pop() == t8.state

    print "Deleting a state object will wich is a current state for tracked "\
          "item will set their current state to none"
    t9, created = TrackedItem.get_tracker_or_create(content_object=l[29])
    assert t9.state == None

    print "It deletes all the states refering to the current object if there"\
          " are several of them"

    t10, created = TrackedItem.get_tracker_or_create(content_object=l[28])
    t11, created = TrackedItem.get_tracker_or_create(content_object=l[27])
    t10.state = p[4]
    t10.save()
    t11.state = p[4]
    t11.save()

    p[4].delete()
    assert t10.states.all().count() == t11.states.all().count() == 0

if __name__ == '__name__':
    test()