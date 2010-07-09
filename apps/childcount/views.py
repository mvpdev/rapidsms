#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os

from datetime import date, timedelta, datetime

import re


from rapidsms.webui.utils import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.utils.translation import gettext_lazy as _, activate
from django.template import Template, Context, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, UserManager, Group
from django import forms
from reporters.models import PersistantConnection, PersistantBackend
from locations.models import Location


from childcount.models import Patient, CHW, Configuration, Clinic
from childcount.models.ccreports import TheCHWReport, ClinicReport
from childcount.models.ccreports import SummaryReport, Week_Summary_Report
from childcount.models.bdntreports import BdnethouseHold
from childcount.utils import clean_names

form_config = Configuration.objects.get(key='dataentry_forms').value
cc_forms = re.split(r'\s*,*\s*', form_config)

@login_required
def dataentry(request):
    ''' displays Data Entry U.I '''
    today = date.today().strftime("%Y-%m-%d")
    chws = CHW.objects.all()
    chw = CHW.objects.get(id=request.user.id)
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


def index(request):
    '''Index page '''
    template_name = "childcount/index.html"
    title = "ChildCount-2.0"
    info = {}
    info.update({"title": title})
    info.update({'risk': nutrition_png(request)})
    info.update(clinic_report(request))
    clinics = Clinic.objects.all()
    info.update({'sms': sms_png(request)})
    info.update({'clinics': clinics})
    info.update({'atrisk': TheCHWReport.total_at_risk(), \
                           'eligible': TheCHWReport.total_muac_eligible()}
    )
    #Summary Report
    sr = SummaryReport.summary()
    info.update(sr)
    #This Week Summary Report
    wsr = Week_Summary_Report.summary()
    info.update(wsr)

    return render_to_response(request, template_name, info)

class CHWForm(forms.Form):
    #username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField()
    language = forms.CharField(min_length=2, max_length=5)
    location = forms.ChoiceField(choices=[(location.id, location.name) \
                                       for location in Location.objects.all()])
    mobile = forms.CharField(required=False)

def add_chw(request):

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
                                                   slug__iexact='dataentry'), \
                                     identity=chw.username, \
                                     reporter=chw, \
                                     last_seen=datetime.datetime.now())
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
                                         last_seen=datetime.datetime.now())
                c.save()

            return HttpResponseRedirect(reverse('childcount.views.index'))
    else:
        form = CHWForm()

    info.update({'form': form})

    return render_to_response(request, 'childcount/add_chw.html', info)

def list_chw(request):

    info = {}
    chews = CHW.objects.all().order_by('-id')
    info.update({'chews': chews})
    return render_to_response(request, 'childcount/list_chw.html', info)


def chw(request):
    '''Community Health Worker page '''
    report_title = CHW._meta.verbose_name
    rows = []
    columns, sub_columns = CHW.table_columns()

    reports = CHW.objects.filter(role__code='chw')
    i = 0
    for report in reports:
        patients = Patient.objects.filter(chw=report)
        num_patients = patients.count()
        num_under_5 = 0
        for person in patients:
            if person.age_in_days_weeks_months()[2] < 60:
                num_under_5 += 1
        i += 1
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]
        row["cells"][-2] = {"value": num_patients}
        row["cells"][-1] = {"value": num_under_5}

        if i == 100:
            row['complete'] = True
            rows.append(row)
            break
        rows.append(row)

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": true },"
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    if request.method == 'GET' and 'excel' in request.GET:
        '''response = HttpResponse(mimetype="application/vnd.ms-excel")
        filename = "%s %s.xls" % \
                   (report_title, datetime.now().strftime("%d%m%Y"))
        response['Content-Disposition'] = "attachment; " \
                                          "filename=\"%s\"" % filename
        from findug.utils import create_excel
        response.write(create_excel(context_dict))
        return response'''
        return render_to_response(request, 'childcount/chw.html', context_dict)
    else:
        return render_to_response(request, 'childcount/chw.html', context_dict)


def patient(request):
    '''Patients page '''
    report_title = Patient._meta.verbose_name
    rows = []
    MAX_PAGE_PER_PAGE = 100
    DEFAULT_PAGE = 1
    columns, sub_columns = Patient.table_columns()

    getpages = Paginator(Patient.objects.all(), 100)
    
    try:
        page = int(request.GET.get('page', DEFAULT_PAGE))
    except ValueError:
        page = 1

    try:
        reports = getpages.page(page)
    except (EmptyPage, InvalidPage):
        reports = getpages.page(getpages.num_pages)

    for report in reports.object_list:
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]
        rows.append(row)
        
        
    #rows.append(row)
        
    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": true },"
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'reports': reports, 'aocolumns_js': aocolumns_js}

    return render_to_response(\
                request, 'childcount/patient.html', context_dict)


def nutrition_png(request):
    nutdata = TheCHWReport.muac_summary()
    return nutdata

    '''
    filename = 'nutrition_summary.png'
    pie = PiePlot(filename, nutdata, 450, 300, shadow=True)
    pie.render()
    pie.commit()
    f = open(filename)
    data = f.read()
    f.close()
    os.unlink(filename)
    response = HttpResponse(mimetype="image/png")
    response.write(data)
    return response
    '''


def sms_png(request):
    data = TheCHWReport.sms_per_day()
    return data
    '''    
    filename = 'sms.png'
    pie = BarPlot(filename, data, 450, 300)
    pie.render()
    pie.commit()
    f = open(filename)
    data = f.read()
    f.close()
    os.unlink(filename)
    response = HttpResponse(mimetype="image/png")
    response.write(data)
    return response
    '''


def bednet_summary(request):
    '''House Patients page '''
    report_title = Patient._meta.verbose_name
    rows = []
    columns, sub_columns = BdnethouseHold.summary()

    reports = BdnethouseHold.return_household()
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]

        rows.append(row)

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": true },"
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    return render_to_response(\
                request, 'childcount/bednet.html', context_dict)

def clinic_report(request):
    '''House Patients page '''
    report_title = ClinicReport._meta.verbose_name
    rows = []
    columns, sub_columns = ClinicReport.summary()

    reports = ClinicReport.objects.all()
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"] = [{'value': \
                        Template(col['bit']).render(Context({'object': \
                            report}))} for col in columns]

        rows.append(row)

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": true },"
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': request.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    return context_dict
