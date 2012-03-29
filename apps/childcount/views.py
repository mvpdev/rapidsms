#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import re
import json
from datetime import date, timedelta, datetime
from urllib import urlencode

from rapidsms.webui.utils import render_to_response

from indicator import Indicator

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _, activate, get_language
from django.utils.translation import check_for_language
from django.utils import simplejson
from django.template import Context, loader
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.db.models import F, Q

from reporters.models import PersistantConnection, PersistantBackend
from locations.models import Location

from childcount.fields import PatientForm
from childcount.models import Patient, CHW, Configuration, Clinic
from childcount.utils import clean_names, get_indicators
from childcount.helpers import site

from reportgen.timeperiods import FourWeeks, Month, TwelveMonths
from reportgen.models import Report


form_config = Configuration.objects.get(key='dataentry_forms').value
cc_forms = re.split(r'\s*,*\s*', form_config)

@login_required
@permission_required('childcount.add_encounter')
def dataentry(request):
    ''' displays Data Entry U.I. '''

    ''' Make default date in the future so that DE clerk is forced
    to manually select a date. '''
    today = (date.today() + timedelta(1)).strftime("%Y-%m-%d")
    chws = CHW.objects.filter(is_active=True)
    try:
        chw = CHW.objects.get(id=request.user.id)
    except CHW.DoesNotExist:
        return redirect(index)
    return render_to_response(request, 'childcount/data_entry.html', \
                              {'chws': chws, 'today': today, \
                               'chw': chw, 'forms': cc_forms})

@login_required
def form(request, formid):
    ''' sends form_id according to user's language '''

    chw = CHW.objects.get(id=request.user.id)
    activate(chw.language)
    form = loader.get_template('childcount/forms/%s.json' % formid)\
                              .render(Context({}))

    return HttpResponse(form, mimetype="application/json")


from childcount import dashboard_sections

DASHBOARD_TEMPLATE_DIRECTORY = "childcount/dashboard_sections"

def dashboard_gather_data(dashboard_template_names):
    """this method is used with the new dashboard_sections templates
    and their corresponding methods in the 'dashboard_sections' module
    """
    data={}
    for tname in dashboard_template_names:
        try:
            data[tname] = getattr(dashboard_sections, tname)()
        except AttributeError:
            data[tname] = False
            print tname
    return data

print ">>>>>>>>>>%s" % get_language()
@login_required
def index(request):
    '''Dashboard page '''
    info = {'title': _(u"ChildCount+ Dashboard")}
    print ">>>>>>>>>>>>>>>%s" % get_language()
    print ">>>>>>>>>>>>>>>%s" % check_for_language('ti')
    info['lang'] = get_language()

    try:
        dashboard_template_names = Configuration.objects.get(key='dashboard_sections').value.split()
    except:
        dashboard_template_names = ['highlight_stats_bar',]
    
    info['dashboard_data'] = dashboard_gather_data(dashboard_template_names)
    info['section_templates'] = ["%s/%s.html" % (DASHBOARD_TEMPLATE_DIRECTORY, ds) for ds in dashboard_template_names]
    
    return render_to_response(request, "childcount/dashboard.html", info)


def site_summary(request, report='site', format='json'):
    if request.is_ajax() and format == 'json':

        period = None
        if report == 'site':
            period = TwelveMonths.periods()[0]
        elif report == 'general_summary':
            period = TwelveMonths.periods()[0]
        elif report == 'month':
            period = Month.periods()[0]
        elif report == 'week':
            period = FourWeeks.periods()[0].sub_periods()[0]
        else:
            print report
            return HttpResponse(status=400)

        if format == 'json':
            mimetype = 'application/javascript'
        data = simplejson.dumps(site.summary_stats(period))
        return HttpResponse(data, mimetype)
    # If you want to prevent non XHR calls
    else:
        return HttpResponse(status=400)


class CHWForm(forms.Form):
    #username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField()
    language = forms.CharField(min_length=2, max_length=5)
    language = forms.ChoiceField(choices=settings.LANGUAGES)
    location = forms.ChoiceField(choices=[(location.id, location.name) \
                                       for location in Location.objects.all()])
    mobile = forms.CharField(required=False)

@login_required
@permission_required('childcount.add_chw')
def add_chw(request):

    if not (request.user.is_staff + request.user.is_superuser):
        redirect(list_chw)

    info = {}

    if request.method == 'POST':
        form = CHWForm(request.POST)
        if form.is_valid():

            #username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password']
            language = form.cleaned_data['language']
            location = form.cleaned_data['location']
            mobile = form.cleaned_data['mobile']

            # CHW creation
            chw = CHW()
            # names and alias
            surname, firstnames, alias = clean_names(u"%s %s" % \
                                  (last_name, first_name), surname_first=True)
            orig_alias = alias[:20]
            alias = orig_alias.lower()
            if alias != chw.alias and not re.match(r'%s\d' % alias, chw.alias):
                n = 1
                while User.objects.filter(username__iexact=alias).count():
                    alias = "%s%d" % (orig_alias.lower(), n)
                    n += 1
                chw.alias = alias
            chw.first_name = firstnames
            chw.last_name = surname
            # properties
            chw.language = language
            chw.location = Location.objects.get(id=location)
            chw.mobile = mobile
            chw.save()

            # set password through User.s
            chw.set_password(password)
            chw.save()

            # Add CHW Group
            chw.groups.add(Group.objects.get(name__iexact='CHW'))

            # create dataentry connection
            c = PersistantConnection(backend=PersistantBackend.objects.get(\
                                                   slug__iexact='debackend'), \
                                     identity=chw.username, \
                                     reporter=chw, \
                                     last_seen=datetime.now())
            c.save()

            # add mobile connection
            try:
                pygsm = PersistantBackend.objects.get(slug__iexact='pygsm')
            except:
                pygsm = PersistantBackend(slug='pygsm', title='pygsm')
                pygsm.save()

            if mobile:
                c = PersistantConnection(backend=pygsm, \
                                         identity=mobile, \
                                         reporter=chw, \
                                         last_seen=datetime.now())
                c.save()

            return HttpResponseRedirect(reverse('childcount.views.index'))
    else:
        form = CHWForm()

    info.update({'form': form})

    return render_to_response(request, 'childcount/add_chw.html', info)

@login_required
@permission_required('childcount.add_chw')
def list_chw(request):

    CHWS_PER_PAGE = 50
    info = {}
    chews = CHW.objects.all().order_by('first_name')
    info.update({'chews': chews})
    paginator = Paginator(chews, CHWS_PER_PAGE)
    page = int(request.GET.get('page', 1))
    info.update({'paginator':paginator.page(page)})

    return render_to_response(request, 'childcount/list_chw.html', info)

@login_required
def patient(request, chw=None):
    '''Patients page '''
    MAX_PAGE_PER_PAGE = 30
    DEFAULT_PAGE = 1
    info = {}
    patients = Patient.objects.all()
    if chw is not None:
        patients = Patient.objects.filter(chw__username=chw)
        info['chw'] = chw
    
    try:
        search = request.GET.get('patient_search','')
    except:
        search = ''
    
    if search:
        if len(search.split()) > 1:
            patients = patients.filter(Q(first_name__search=search,\
                               last_name__search=search) | \
                               Q(health_id__search=search))
        else:
            patients = patients.filter(Q(first_name__search=search)|\
                               Q(last_name__search=search)|\
                               Q(health_id__search=search))

    paginator = Paginator(patients, MAX_PAGE_PER_PAGE)

    try:
        page = int(request.GET.get('page', DEFAULT_PAGE))
    except:
        page = DEFAULT_PAGE
    
    info['rcount'] = patients.count()
    info['rstart'] = paginator.per_page * page
    info['rend'] = (page + 1 * paginator.per_page) - 1
    
    
    try:
        info['patients'] = paginator.page(page)
    except:
        info['patients'] = paginator.page(paginator.num_pages)

    #get the requested page, if its out of range display last page
    try:
        current_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        current_page = paginator.page(paginator.num_pages)

    nextlink, prevlink = {}, {}

    if paginator.num_pages > 1:
        nextlink['page'] = info['patients'].next_page_number()
        prevlink['page'] = info['patients'].previous_page_number()

        info.update(pagenator(paginator, current_page))

    if search != '':
        info['search'] = search
        nextlink['search'] = search
        prevlink['search'] = search
    
    info['prevlink'] = urlencode(prevlink)
    info['nextlink'] = urlencode(nextlink)

    return render_to_response(\
                request, 'childcount/patient.html', info)


def pagenator(getpages, reports):
    LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
    LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
    NUM_PAGES_OUTSIDE_RANGE = 2
    ADJACENT_PAGES = 4

    if(getpages.num_pages > 1):
        " Initialize variables "
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)

        if (getpages.num_pages <= LEADING_PAGE_RANGE_DISPLAYED):
            in_leading_range = in_trailing_range = True
            page_numbers = [n for n in range(1, \
                  getpages.num_pages + 1) if n > 0 and n <= getpages.num_pages]
        elif (reports.number <= LEADING_PAGE_RANGE):
            in_leading_range = True
            page_numbers = [n for n in range(1,\
                         LEADING_PAGE_RANGE_DISPLAYED + 1) \
                         if n > 0 and n <= getpages.num_pages]
            pages_outside_leading_range = [n + getpages.num_pages\
                         for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif (reports.number > getpages.num_pages - TRAILING_PAGE_RANGE):
            in_trailing_range = True
            page_numbers = [n for n in range(\
            getpages.num_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, \
            getpages.num_pages + 1) if n > 0 and n <= getpages.num_pages]
            pages_outside_trailing_range = [n + 1 for n in range(0, \
                                    NUM_PAGES_OUTSIDE_RANGE)]
        else:
            page_numbers = [n for n in range(\
                    getpages.num_pages - ADJACENT_PAGES, \
                    getpages.num_pages + ADJACENT_PAGES + 1) \
                    if n > 0 and n <= getpages.num_pages]
            pages_outside_leading_range = [n + getpages.num_pages \
                            for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [n + 1 for n in range(0, \
                            NUM_PAGES_OUTSIDE_RANGE)]

        return {
            "is_paginated": getpages.num_pages > 1,
            "previous": reports.previous_page_number(),
            "has_previous": reports.has_previous(),
            "next": reports.next_page_number(),
            "has_next": reports.has_next(),
            "page": reports.number,
            "pages": getpages.num_pages,
            "page_numbers": page_numbers,
            "last_page": getpages.num_pages,
            "in_leading_range": in_leading_range,
            "in_trailing_range": in_trailing_range,
            "pages_outside_leading_range": pages_outside_leading_range,
            "pages_outside_trailing_range": pages_outside_trailing_range}

@login_required
@permission_required('childcount.change_patient')
def edit_patient(request, healthid):
    if healthid is None:
        # Patient to edit was submitted 
        if 'hid' in request.GET:
            return HttpResponseRedirect( \
                "/childcount/patients/edit/%s/" % \
                    (request.GET['hid'].upper()))
        # Need to show patient select form
        else:
            return render_to_response(request,
                'childcount/edit_patient.html', {})
    else: 
        # Handle invalid health IDs
        try:
            patient = Patient.objects.get(health_id=healthid)
        except Patient.DoesNotExist:
            return render_to_response(request,
                'childcount/edit_patient.html', { \
                'health_id': healthid.upper(),
                'failed': True})

        # Save POSTed data
        if request.method == 'POST':
            form = PatientForm(request.POST, instance=patient)
            if form.is_valid():
                print 'saving'
                print form.save(commit=True)
                print patient.household
                return render_to_response(request,
                    'childcount/edit_patient.html', { \
                    'health_id': healthid.upper(),
                    'patient': patient,
                    'success': True})
        # Show patient edit form (nothing saved yet)
        else:
            form = PatientForm(instance=patient)
        return render_to_response(request, 
            'childcount/edit_patient.html', { \
            'form': form,
            'patient': patient,
            'health_id': patient.health_id.upper()
        })


def chw_json(request):
    chws = CHW.objects.all()
    chwlist = []
    for chw in chws:
        chwlist.append({'pk': chw.pk,'name': chw.__unicode__()})

    json_data = json.dumps(chwlist)
    return HttpResponse(json_data, mimetype="application/json")

@login_required
def indicators(request):
    i=0
    indicators = []
    for mems in get_indicators():
        data = []
        for m in mems['inds']:
            if hasattr(m[1].type_in, '__name__'):
                tin = str(m[1].type_in.__name__)
            else:
                tin = str(m[1].type_in.__class__.__name__) + \
                    "(" + str(m[1].type_in.mtype.__name__) + ")"

            if hasattr(m[1].type_out, '__name__'):
                tout = str(m[1].type_out.__name__)
            else:
                tout = str(m[1].type_out.__class__.__name__)

            data.append({
                'slug': m[0],
                'cls': m[1],
                'type_in': tin,
                'type_out': tout,
                'variant_index': "_"+mems['slug']+"_"+m[1].slug,
                'output_is_number': m[1].output_is_number(),
                'input_is_query_set': m[1].input_is_query_set(),
            })

            i += 1

        indicators.append({'name': mems['name'],
                        'slug': mems['slug'],
                        'members': data})

    return render_to_response(request, 
            'childcount/indicators.html', { \
            'indicators': indicators,
            'report_pk': Report.objects.get(classname='IndicatorChart').pk
        })


'''
@login_required
def autocomplete(request):
    def iter_results(results):
        if results:
            for r in results:
                yield '%s|%s\n' % (r.health_id.upper(), r.id)
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    patients = Patient.objects.filter(health_id__startswith=q)[:limit]
    return HttpResponse(iter_results(patients), mimetype='text/plain')
'''


class ChangeCHWForm(forms.Form):
    chw = forms.ChoiceField(choices=[(chw.id, chw.full_name()) \
                                       for chw in CHW.objects.all()])


def change_chw(request, chw):
    info = {}
    try:
        chw = CHW.objects.get(username=chw)
    except CHW.DoesNotExist:
        return redirect(index)
    if request.method == 'POST':
        form = ChangeCHWForm(request.POST)
        if form.is_valid():
            chw_id = form.cleaned_data['chw']
            try:
                nchw = CHW.objects.get(id=chw_id)
            except CHW.DoesNotExist:
                info['status'] = _(u"CHW does not exist!")
            else:
                patients = Patient.objects.filter(chw=chw)
                count = patients.count()
                patients.update(chw=nchw)
                status = _(u"%(num)s patients have been migrated to %(chw)s" \
                    % {'num': count, 'chw': nchw.full_name()})
                info['status'] = status
                form = None
    else:
        form = ChangeCHWForm()
    info['form'] = form
    info['chw'] = chw
    return render_to_response(\
                request, 'childcount/change_chw.html', info)
