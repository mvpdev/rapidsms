#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from operator import itemgetter

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import NoReverseMatch

from rapidsms.webui.utils import render_to_response

from findtb.models import SlidesBatch, Role, FINDTBGroup, FINDTBLocation

from locations.models import Location
from reporters.models import Reporter

from django_tracking.models import State, TrackedItem


@login_required
def eqa_tracking(request, *arg, **kwargs):

    # selecting slides batch
    id = kwargs.get('id', 0)
    dtu = get_object_or_404(Location, pk=id)

    quarter = kwargs.get('quarter', None)
    if not quarter:
        quarter, year = SlidesBatch.get_quarter()
    else:
        year = quarter = kwargs['year']

    # TODO: time pagination

    try:
        slides_batch = SlidesBatch.objects.get_for_quarter(dtu, quarter, year)
    except SlidesBatch.DoesNotExist:
        events = []
        contacts = []
    else:

        tracked_item, created = TrackedItem.get_tracker_or_create(content_object=slides_batch)        

        try:
            return redirect("findtb-eqa-%s" % tracked_item.state.title, id=id, 
                             year=year, quarter=quarter )
        except NoReverseMatch:
            pass
        
        
        # getting specimen related event to look at, filtered by type
        events = tracked_item.get_history()

        #  getting slides currently in EQA
        states = State.objects.filter(is_final=False, origin='eqa',
                                      is_current=True).order_by('-created')

    contacts = Role.getSlidesBatchRelatedContacts(slides_batch)

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

    return render_to_response(request, "eqa/eqa-tracking.html", ctx)

@login_required
def controllers(request, *arg, **kwargs):
    first_group = FINDTBGroup.objects.get(name=\
                        FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME)
    second_group = FINDTBGroup.objects.get(name=\
                        FINDTBGroup.SECOND_CONTROL_FOCAL_PERSON_GROUP_NAME)

    dtus = []
    for loc in FINDTBLocation.objects.filter(type__name='dtu'):
        dtu = {'id':loc.id, 'name':loc.name, 'zone':loc.get_zone().name, \
               'district':loc.get_district().name}
        try:
            dtu['1st'] = \
                    Role.objects.get(location=loc, group=first_group).reporter
        except Role.DoesNotExist:
            dtu['1st'] = None
        try:
            dtu['2nd'] = \
                    Role.objects.get(location=loc, group=second_group).reporter
        except Role.DoesNotExist:
            dtu['2nd'] = None
        dtus.append(dtu)

    dtus.sort(key=itemgetter('zone','district'))

    first_controllers = Reporter.objects.filter(\
                                        role__in=first_group.role_set.all())
    second_controllers = Reporter.objects.filter(\
                                        role__in=second_group.role_set.all())
    ctx = {'dtus':dtus, '1sts':first_controllers, '2nds':second_controllers}

    return render_to_response(request, "eqa/eqa-controllers.html", ctx)
