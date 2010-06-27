#!/usr/bin/env python
# -*- coding= UTF-8 -*-


import random
import datetime

# we use rapidsms render_to_response wiwh is a wrapper giving access to
# some additional data such as rapidsms base templates
# careful : first parameter must be the request, not a template
from rapidsms.webui.utils import render_to_response
from locations.models import Location

from django.core.urlresolvers import reverse
from django_tracking.models import TrackedItem
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from findtb.libs.utils import send_to_dtu, get_specimen_by_status
from findtb.models import SpecimenInvalid, SpecimenMustBeReplaced
from django_tracking.models import State
from findtb.models import Specimen, Role, SlidesBatch


@login_required
def eqa_dashboard(request, *arg, **kwargs):

    # get navigation data
    event_type = kwargs.get('event_type', 'alert')\
              or request.session.get('event_type', 'alert')
    request.session['event_type'] = event_type
    events_url = reverse(kwargs['view_name'], args=(event_type,))

    quarter, year = SlidesBatch.get_quarter(datetime.date.today())

    # calculating pagination in the 'see more' link
    # Fix: incremental pagination doesn't increment
    try:
        events_count = int(request.GET.get('events_count', 10))
        events_inc = int((request.GET.get('events_inc', 5) or 5))
    except TypeError:
        events_count = 10
        events_inc = 5

    # getting specimen related event to look at, filtered by type
    all_events = events = State.objects.filter(origin='eqa').order_by('-created')

    if event_type == 'alert':
        events = State.objects.filter(is_final=False,
                                      origin='sref',
                                     is_current=True)\
                              .filter(type=event_type).order_by('-created')

    # checking if we should display the link 'see more' while limiting
    # the output
    next_events = events[:events_count + events_inc]
    events = events[:events_count]
    more_events = next_events.count() > events.count()

    # 'see more' display more and more events at every clic
    events_count += events_inc

    #  getting slides you should look at, grouped by dtu
    states = State.objects.filter(is_final=False, origin='eqa',
                                  is_current=True).order_by('-created')

    # get data for the right navigation pannel
    districts = Location.objects.filter(type__name=u"district")
    zones = Location.objects.filter(type__name=u"zone")
    dtus = (state.content_object.slides_batch.location for state in states)

    zone = request.POST.get('zone', None)
    if zone:
        selected_zone = zone
    else:
        selected_zone = request.session.get('zone', 'all')
    if selected_zone != 'all':
         selected_zone = int(selected_zone)
         districts = districts.filter(parent__pk=selected_zone)
         dtus = (dtu for dtu in dtus if dtu.parent.parent.pk == selected_zone)

    district = request.POST.get('district', None)
    if district:
        selected_district = district
        if district != 'all':
            selected_zone = Location.objects.get(pk=selected_district).parent.pk
    else:
        selected_district = request.session.get('district', 'all')
    if selected_district != 'all':
        selected_district = int(selected_district)
        dtus = (dtu for dtu in dtus if dtu.parent.pk == selected_district)

    dtus = list(dtus)

    request.session['district'] = selected_district
    request.session['zone'] = selected_zone




    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "eqa/eqa-dashboard.html", ctx)


@login_required
def sref_dashboard(request, *arg, **kwargs):

    # get navigation data

    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'])

    event_type = kwargs.get('event_type', 'alert')\
                 or request.session.get('event_type', 'alert')
    request.session['event_type'] = event_type
    events_url = reverse(kwargs['view_name'], args=(event_type,))


    # calculating pagination in the 'see more' link
    # Fix: incremental pagination doesn't increment
    try:
        events_count = int(request.GET.get('events_count', 10))
        events_inc = int((request.GET.get('events_inc', 5) or 5))
    except TypeError:
        events_count = 10
        events_inc = 5

    # getting specimen related event to look at, filtered by type
    all_events = events = State.objects.filter(origin='sref').order_by('-created')

    if event_type == 'alert':
        events = State.objects.filter(is_final=False,
                                      origin='sref',
                                      is_current=True)\
                      .filter(type=event_type).order_by('-created')

    # checking if we should display the link 'see more' while limiting
    # the output
    next_events = events[:events_count + events_inc]
    events = events[:events_count]
    more_events = next_events.count() > events.count()

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    # 'see more' display more and more events at every clic
    events_count += events_inc

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-dashboard.html", ctx)


@login_required
def eqa_tracking(request, *args, **kwargs):

    events = [{"title": "Pajimo HC III results have been cancelled",
                          "type": "cancelled", "date": "3 hours ago"},
             {"title": "Pajimo HC III results are completed",
              "type": "checked", "date": "Yesterday"},
             {"title": "Pajimo HC III slides have arrived at NTRL",
                              "type": "notice", "date": "2 hours ago"},
             {"title": "Pajimo HC III slides are 3 days late",
              "type": "warning", "date": "2 days ago"},
           ]

    previous_quarter = True
    next_quarter = True
    current_quarter = True

    batchs = ["#%s" % random.randint(1000, 9999) for x in range(5)]

    # TODO : don't make the second controle mandatory  since it the first
    # ones agree, there is no need to check
    # make it even grey in the UI in that case
    # Carefull to what "agree" mean : it's not just stricly equal results
    possible_results = ("Choose", "Negative","1+", "2+", "3+") +\
                        tuple("%s AFB" % x for x in range(1, 20))


    batch_arrived = True

    slides = ["%s/09-150210" % random.randint(1000, 9999) for x in range(10)]


    districts = Location.objects.filter(type__name=u"district")
    zones = Location.objects.filter(type__name=u"zone")
    dtus = Location.objects.filter(parent=districts[0])

    batch_arrives = True

    types = ["DTU", "DTLS", "DLAB", "DLFP"]
    names = ["Keyta", "Kamara", "Camara", "Dolo", "Cissoko"]
    contacts = []
    for x in range(0, random.randint(0, 5)) :
        contacts.append({"type": types.pop(), "name": names.pop()})

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())


    return render_to_response(request, "eqa/eqa-tracking.html", ctx)


@login_required
def sref_tracking(request, *args, **kwargs):

    specimen = get_object_or_404(Specimen, pk=kwargs.get('id', 0))
    ti, c = TrackedItem.get_tracker_or_create(content_object=specimen)

    return redirect("findtb-sref-%s" % ti.state.title, id=kwargs['id'])


@login_required
def search(request, *arg, **kwargs):


    districts = Location.objects.filter(type__name=u"district")
    eqa = Location.objects.filter(parent=districts[0])
    sref = Location.objects.filter(parent=districts[1])

    results = [[], []]

    for dtu in eqa:
        result = {"specimen": "%s/09-150210" % random.randint(11111, 99999),
                  "dtu": dtu}
        results[0].append(result)

    for dtu in sref:
        result = {"specimen": "%s/09-150210" % random.randint(11111, 99999),
                  "dtu": dtu}
        results[1].append(result)


    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())


    return render_to_response(request, "findtb-search.html", ctx)


@login_required
def sref_invalidate(request, *args, **kwargs):

    id = kwargs.get('id', 0)

    specimen = get_object_or_404(Specimen, pk=id)
    tracked_item, created = TrackedItem.get_tracker_or_create(content_object=specimen)

    # get navigation data
    #TODO: put this code in a function
    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'], args=(id,))

    request_new = bool(request.GET.get('request_new', 0))
    confirm = bool(request.GET.get('confirm', 0))

    if confirm:

        result = SpecimenInvalid(cause='invalid', specimen=specimen)

        if request_new:
            msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                       u"has been declared invalid by NTRL. "\
                       u"Please send a new specimen." %\
                       {'patient': specimen.patient,
                        'tag': specimen.tracking_tag}

            tracked_item.state = State(content_object=result)
            tracked_item.save()

            result = SpecimenMustBeReplaced(specimen=specimen)
            tracked_item.state = State(content_object=result, is_final=True)
            tracked_item.save()

        else:
            msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                       u"has been declared invalid by NTRL. "\
                       u"There is nothing to do." %\
                       {'patient': specimen.patient,
                        'tag': specimen.tracking_tag}

            tracked_item.state = State(content_object=result, is_final=True)
            tracked_item.save()

        send_to_dtu(specimen.location, msg)

        return redirect("findtb-sref-tracking", id=specimen.id)


    contacts = Role.getSpecimenRelatedContacts(specimen)

    form_class = tracked_item.state.content_object.get_web_form()

    events = tracked_item.get_history()

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-invalidate.html", ctx)


@login_required
def sref_done(request, *args, **kwargs):

    id = kwargs.get('id', 0)

    specimen = get_object_or_404(Specimen, pk=id)
    tracked_item, created = TrackedItem.get_tracker_or_create(content_object=specimen)

    if tracked_item.state.title != 'done':
        return redirect("findtb-sref-tracking", id=kwargs['id'])

    # get navigation data
    #TODO: put this code in a function
    task = request.GET.get('task', None)\
           or request.session.get('task', 'Incoming')
    request.session['task'] = task
    task_url = reverse(kwargs['view_name'], args=(id,))

    request_new = bool(request.GET.get('request_new', 0))
    confirm = bool(request.GET.get('confirm', 0))

    contacts = Role.getSpecimenRelatedContacts(specimen)

    form_class = tracked_item.state.content_object.get_web_form()

    events = tracked_item.get_history()

    # getting the list of specimens to test
    specimens = get_specimen_by_status()
    displayed_specimens = specimens[task]

    ctx = {}
    ctx.update(kwargs)
    ctx.update(locals())

    return render_to_response(request, "sref/sref-done.html", ctx)
