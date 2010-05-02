#!/usr/bin/env python
# -*- coding= UTF-8 -*-


import random
# we use rapidsms render_to_response wiwh is a wrapper giving access to
# some additional data such as rapidsms base templates
# careful : first parameter must be the request, not a template
from rapidsms.webui.utils import render_to_response
from locations.models import Location, LocationType
from django_tracking.models import State
from findtb.models import Specimen

def eqa_bashboard(request, *arg, **kwargs):

    events = [{"title": "Namokora HC IV slides have arrived",
               "type": "notice", "date": "2 hours ago"},
               {"title": "Pajimo HC III results have been cancelled",
                            "type": "cancelled", "date": "3 hours ago"},
               {"title": "Pajimo HC III results are completed",
                "type": "checked", "date": "Yesterday"},
               {"title": "Namokora HC IV slides are 3 days late",
                "type": "warning", "date": "2 days ago"},
             ]


    districts = Location.objects.filter(type__name=u"district")
    zones = Location.objects.filter(type__name=u"zone")
    dtus = Location.objects.filter(parent=districts[0])

    ctx = {}
    ctx.update(locals())
    ctx.update(kwargs)

    return render_to_response(request, "eqa-dashboard.html", ctx)


def sref_bashboard(request, *arg, **kwargs):

    
    states = State.objects.all().order_by('-created')[:10]

    districts = Location.objects.filter(type__name=u"district")
    zones = Location.objects.filter(type__name=u"zone")
    

    # looking for specimen that are not in final state
    states = State.objects.filter(final=False)
    dtus = {}
    for state in states:
        if isinstance(state.tracked_item.content_object, Specimen):
            specimen = state.tracked_item.content_object
            dtu = specimen.location
            specimens = dtus.get(dtu.id, [])
            specimens.append(specimen)
            dtus[dtu.id] = specimens
            
    # looking for specimen that are not in final state
    states = State.objects.filter(final=False).order_by('-created')[:10]
    ctx = {}
    ctx.update(locals())
    ctx.update(kwargs)

    return render_to_response(request, "sref-dashboard.html", ctx)


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
    ctx.update(locals())
    ctx.update(kwargs)

    return render_to_response(request, "eqa-tracking.html", ctx)


def sref_tracking(request, *args, **kwargs):


    events = [{"title": "Microscopy of specimen 1234/09-150210 from Namokora HC IV is positive",
                        "type": "notice", "date": "3 hours ago"},

           {"title": "Specimen 1234/09-150210 from Namokora HC IV have arrived at NTRL",
                            "type": "notice", "date": "2 hours ago"},
           {"title": "Specimen 1234/09-150210 from Namokora HC IV is 3 days late",
            "type": "warning", "date": "2 days ago"},
         ]

    districts = Location.objects.filter(type__name=u"district")
    zones = Location.objects.filter(type__name=u"zone")
    dtus = Location.objects.filter(parent=districts[0])

    specimens = []
    for dtu in dtus:
        number = random.randint(11111, 99999)
        specimen = "%s/09-150210 from %s" % (number, dtu)
        specimens.append(specimen)

    batch_arrives = True

    types = ["DTU", "DTLS", "DLAB", "DLFP"]
    names = ["Keyta", "Kamara", "Camara", "Dolo", "Cissoko"]
    contacts = []
    for x in range(0, random.randint(0, 5)) :
        contacts.append({"type": types.pop(), "name": names.pop()})

    ctx = {}
    ctx.update(locals())
    ctx.update(kwargs)

    return render_to_response(request, "sref-tracking.html", ctx)


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
    ctx.update(locals())
    ctx.update(kwargs)

    return render_to_response(request, "findtb-search.html", ctx)
