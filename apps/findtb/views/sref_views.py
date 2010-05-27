#!/usr/bin/env python
# -*- coding= UTF-8 -*-


# we use rapidsms render_to_response wiwh is a wrapper giving access to
# some additional data such as rapidsms base templates
# careful : first parameter must be the request, not a template
from rapidsms.webui.utils import render_to_response

from findtb.models import Specimen, Role
from findtb.libs.utils import get_specimen_by_status

from django.core.urlresolvers import reverse
from django_tracking.models import TrackedItem
from django.shortcuts import get_object_or_404, redirect



def sref_incoming(request, *args, **kwargs):

    id = kwargs.get('id', 0)

    specimen = get_object_or_404(Specimen, pk=id)
    tracked_item, created = TrackedItem.get_tracker_or_create(content_object=specimen)

    if tracked_item.state.title != 'incoming':
        return redirect("findtb-sref-tracking", id=kwargs['id'])

    # get navigation data
    #TODO: put this code in a function
    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'], args=(id,))

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    contacts = Role.getSpecimenRelatedContacts(specimen)

    form_class = tracked_item.state.content_object.get_web_form()

    if request.method == 'POST':
       form = form_class(data=request.POST, specimen=specimen)

       if form.is_valid():
            form.save()
            ti, created = TrackedItem.get_tracker_or_create(content_object=specimen)
            return redirect("findtb-sref-%s" % ti.state.title, id=specimen.id)
    else:
        form = form_class(specimen=specimen)

    events = tracked_item.get_history()

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-incoming.html", ctx)



def sref_invalid(request, *args, **kwargs):

    id = kwargs.get('id', 0)

    specimen = get_object_or_404(Specimen, pk=id)
    tracked_item, created = TrackedItem.get_tracker_or_create(content_object=specimen)

    contacts = Role.getSpecimenRelatedContacts(specimen)

    if tracked_item.state.title != 'invalid':
        return redirect("findtb-sref-tracking", id=kwargs['id'])

    # get navigation data

    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'], args=(id,))

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    events = tracked_item.get_history()

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-invalid.html", ctx)


def sref_received(request, *args, **kwargs):

    id = kwargs.get('id', 0)

    specimen = get_object_or_404(Specimen, pk=id)
    tracked_item, created = TrackedItem.get_tracker_or_create(content_object=specimen)

    if tracked_item.state.title != 'received':
        return redirect("findtb-sref-tracking", id=kwargs['id'])

    # get navigation data

    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'], args=(id,))

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    contacts = Role.getSpecimenRelatedContacts(specimen)

    form_class = tracked_item.state.content_object.get_web_form()

    if request.method == 'POST':
       form = form_class(data=request.POST, specimen=specimen)

       if form.is_valid():
            form.save()
            ti, created = TrackedItem.get_tracker_or_create(content_object=specimen)
            return redirect("findtb-sref-%s" % ti.state.title, id=specimen.id)
    else:
        form = form_class(specimen=specimen)

    events = tracked_item.get_history()

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-received.html", ctx)



def sref_microscopy(request, *args, **kwargs):

    id = kwargs.get('id', 0)

    specimen = get_object_or_404(Specimen, pk=id)
    tracked_item, created = TrackedItem.get_tracker_or_create(content_object=specimen)

    if tracked_item.state.title != 'microscopy':
        return redirect("findtb-sref-tracking", id=kwargs['id'])

    # get navigation data

    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'], args=(id,))

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    contacts = Role.getSpecimenRelatedContacts(specimen)

    form_class = tracked_item.state.content_object.get_web_form()

    #isinstance doesn't work cause the class is a a factory
    if form_class.__name__ == 'LpaForm':
        current_test = 'LPA'
    else:
        current_test = 'MGIT'

    if request.method == 'POST':
       form = form_class(data=request.POST, specimen=specimen)

       if form.is_valid():
            form.save()
            ti, created = TrackedItem.get_tracker_or_create(content_object=specimen)
            return redirect("findtb-sref-%s" % ti.state.title, id=specimen.id)
    else:
        form = form_class(specimen=specimen)

    events = tracked_item.get_history()

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-microscopy.html", ctx)


