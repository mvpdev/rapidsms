#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response
from django.db.models import ObjectDoesNotExist, Q
from django.contrib.auth.models import User, Group
from datetime import datetime, timedelta
from childcount.forms.general import MessageForm

from childcount.forms.login import LoginForm
from childcount.shortcuts import as_html, login_required
from childcount.models.logs import log, MessageLog, EventLog
from childcount.models.general import Case
from childcount.models.reports import ReportCHWStatus, ReportAllPatients
from muac.models import ReportMalnutrition
from mrdt.models import ReportMalaria
from locations.models import Location
from reporters.models import Reporter, Role

from childcount.utils import day_end, day_start, month_end, next_month

from libreport.pdfreport import PDFReport
from reportlab.lib.units import inch

from django.utils.translation import ugettext_lazy as _
from django.template import Template, Context
from django.template.loader import get_template
from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect

from tempfile import mkstemp
from datetime import datetime, timedelta, date
import os
import csv
import StringIO


from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()
Elements = []

HeaderStyle = styles["Heading1"] # XXXX

def header(txt, style=HeaderStyle, klass=Paragraph, sep=0.3):
    
    '''Creates a reportlab PDF element and adds it to the global Elements list
    
    style - can be a HeaderStyle, a ParaStyle or a custom style, default HeaderStyle
    klass - the reportlab Class to be called, default Paragraph
    sep    - space separator height
    
    '''
    s = Spacer(0.2*inch, sep*inch)
    Elements.append(s)
    para = klass(txt, style)
    Elements.append(para)

#Paragraph Style
ParaStyle = styles["Normal"]

def p(txt):

    '''Create a text Paragraph using  ParaStyle'''
    
    return header(txt, style=ParaStyle, sep=0.1)

#Preformatted Style
PreStyle = styles["Code"]

def pre(txt):
    
    '''Create a text Preformatted Paragraph using  PreStyle'''
    
    s = Spacer(0.1*inch, 0.1*inch)
    Elements.append(s)
    p = Preformatted(txt, PreStyle)
    Elements.append(p)

app = {}
app['name'] = "ChildCount:Health"


@login_required
def reports(request):
    
    '''Lists Reports that can be generated in childcount'''
    
    template_name="childcount/reports/reports.html"
    
    clinics = Location.objects.filter(type__name="Clinic")
    
    zones = Case.objects.order_by("location").values('location', 'location__name').distinct()
    p = Case.objects.order_by("location").values('reporter', 'reporter__first_name', 'reporter__last_name', 'location').distinct()
    providers = []
    for provider in p:
        tmp = {}
        tmp['id'] = provider['reporter']
        tmp['name'] = provider['reporter__last_name'] + " " + provider['reporter__first_name']
        tmp['zone'] = provider['location']
        providers.append(tmp)  
        
    now = datetime.today()
    first   = Case.objects.order_by('created_at')[:1][0]
    date    = first.created_at

    months=[]
    tab_mois=range(1,61,1)
    while ((now - date).days > 0):
        months.append({'id': date.strftime("%m%Y"), 'label': date.strftime("%B %Y"), 'date': date})
        date = next_month(date)
    
    context = {
        "app": app,
        "clinics": clinics,
        "providers": providers,
        "zones": zones,
        "months": months,
        "lesmois": tab_mois
    }
    return render_to_response(request, template_name, context)

@login_required
def last_30_days(request, object_id=None, per_page="0", rformat="pdf", d="30"):
    
    '''A pdf report of chw perfomance within the last 30 days'''
    
    pdfrpt = PDFReport()
    d = int(d)
    pdfrpt.enableFooter(True)
    thirty_days = timedelta(days=d)
    ninty_days = timedelta(days=90)
    today = date.today()
    
    duration_start = today - thirty_days
    muac_duration_start = today - ninty_days
    duration_end = today
    
    pdfrpt.setTitle("ChildCount Kenya: CHW 30 Day Performance Report, from %s to %s"%(duration_start, duration_end))
    
    if object_id is None:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.get_providers_by_clinic(duration_start, duration_end, muac_duration_start, clinic)
            c = clinic
            pdfrpt.setTableData(queryset, fields, c.name, [0.3*inch, 1*inch,0.8*inch,0.8*inch, .8*inch,.8*inch,0.8*inch, 1*inch,1*inch,1*inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.get_providers_by_clinic(duration_start, duration_end, muac_duration_start, object_id)
        c = object_id
        
        if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
            file_name = c.name + ".csv"
            file_name = file_name.replace(" ","_").replace("'","")
            return handle_csv(request, queryset, fields, file_name)
        
        pdfrpt.setTableData(queryset, fields, c.name)
    
    return pdfrpt.render()

@login_required
def muac_summary(request, object_id=None, per_page="0", rformat="pdf", d="30"):
    
    '''A pdf report of chw perfomance within the last 30 days'''
    
    pdfrpt = PDFReport()
    d = int(d)
    pdfrpt.enableFooter(True)
    thirty_days = timedelta(days=d)    
    today = date.today()
    
    duration_start = today - thirty_days
    duration_start = duration_start.replace(day=1)
    duration_end = today
    
    duration_str = "CMAM Summary from %s to %s"%(duration_start.strftime("%d %B, %Y"), today.strftime("%d %B, %Y"))
    
    pdfrpt.setTitle("ChildCount Kenya: CHW 30 Day Performance Report, from %s to %s"%(duration_start, duration_end))
    
    if object_id is None:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.muac_summary(duration_start, duration_end, clinic)
            title = "%s : %s"%(clinic.name, duration_str)
            pdfrpt.setTableData(queryset, fields, title, [0.3*inch, 1*inch,0.8*inch,0.8*inch, .8*inch,.8*inch,0.8*inch, 1*inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.muac_summary(duration_start, duration_end, object_id)
        c = object_id
        
        if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
            file_name = c.name + ".csv"
            file_name = file_name.replace(" ","_").replace("'","")
            return handle_csv(request, queryset, fields, file_name)
        title = "%s : %s"%(c.name, duration_str)
        pdfrpt.setTableData(queryset, fields, title)
    
    return pdfrpt.render()

@login_required
def measles_summary(request, object_id=None, per_page="0", rformat="pdf", d="30"):
    
    '''A summary of measles report per clinic - pdf formart'''
    
    pdfrpt = PDFReport()
    d = int(d)
    pdfrpt.enableFooter(True)
    
    thirty_days = timedelta(days=d)
    ninty_days = timedelta(days=90)
    today = date.today()
    
    duration_start = today - thirty_days
    muac_duration_start = today - ninty_days
    duration_end = today
    
    #pdfrpt.setTitle("RapidResponse MVP Kenya: CHW 30 Day Performance Report, from %s to %s"%(duration_start, duration_end))
    pdfrpt.setTitle("Measles Campaign Summary")
    if object_id is None:
        # clinics = Provider.objects.values('clinic').filter(role=1).distinct()
        
        clinics = Location.objects.filter(type__name="Clinic")
        
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.measles_summary(duration_start, duration_end, muac_duration_start, clinic)
            
            pdfrpt.setTableData(queryset, fields, clinic)
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
        clinic = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.measles_summary(duration_start, duration_end, muac_duration_start, clinic)
        
        
        if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
            file_name = clinic + ".csv"
            file_name = file_name.replace(" ","_").replace("'","")
            return handle_csv(request, queryset, fields, file_name)
        
        pdfrpt.setTableData(queryset, fields, clinic)
    
    return pdfrpt.render()

@login_required
def patients_by_chw(request, object_id=None, per_page="0", rformat="pdf"):
    
    '''List of Cases/Patient per CHW'''
    
    today = datetime.now().strftime("%d %B,%Y")
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(True)
    pdfrpt.setTitle("ChildCount Kenya: Cases Reports by CHW as of %s"%today)
    pdfrpt.setNumOfColumns(2)
    if object_id is None:        
        if request.POST and request.POST['zone']:
            providers = Case.objects.filter(location=request.POST['zone']).values('reporter', 'location').distinct()
            per_page = "1"
        else:
            providers = Case.objects.order_by("location").values('reporter', 'location').distinct()
            providers = Reporter.objects.order_by("location").all()
        for reporter in providers:
            queryset, fields = ReportAllPatients.by_provider(reporter)
            if queryset:
                c = "%s: %s %s: %s"%(reporter.location, reporter.last_name, reporter.first_name, today)
                pdfrpt.setTableData(queryset, fields, c, [0.3*inch, 0.4*inch,1*inch,0.4*inch,0.3*inch, 0.4*inch,0.5*inch,1*inch,1*inch])
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
                    pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']        
        reporter = Reporter.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.by_provider(reporter)
        if queryset:
            c = "%s: %s %s : %s"%(reporter.location, reporter.last_name, reporter.first_name,today)
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = reporter.last_name + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, c, [0.3*inch, 0.4*inch,1*inch,0.4*inch,0.3*inch, 0.4*inch,0.5*inch,1*inch,1*inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("report_per_page")
    
    return pdfrpt.render()
@login_required
#Modification Assane new
def patients_by_age(request, object_id=None, per_page="0", rformat="pdf"):
    
    ''' Children Screening per age for SN CC '''
    
    pdfrpt = PDFReport()
    
    pdfrpt.setTitle("ChildCount Senegal: Listing Enfant par Age")
    #pdfrpt.setRowsPerPage(66)
    pdfrpt.setNumOfColumns(1)
    pdfrpt.setLandscape(True)
    
    if object_id is None and not request.POST:
        age_mois=0
        cases = Case.objects.order_by("location").distinct()
        queryset, fields = ReportAllPatients.by_age(age_mois,cases)
        subtitle = "Registre des Enfants pour: " #%(site.name)
        pdfrpt.setTableData(queryset, fields, subtitle, [0.2*inch, 1.5*inch,0.3*inch,0.7*inch, 0.3*inch,1.5*inch, 0.5*inch, 0.7*inch,0.5*inch, 0.5*inch,0.5*inch,1.5*inch,1*inch])
        if (int(per_page) == 1) is True:
            pdfrpt.setPageBreak()
            pdfrpt.setFilename("Listing_Enfant")
        
    else:
        cases = Case.objects.order_by("location").distinct() 
              
        if request.POST['age']:
            age_mois = int(request.POST['age'])
            str_age=request.POST['age']

            queryset, fields = ReportAllPatients.by_age(age_mois,cases)
        
            subtitle = "Registre des Enfants de : %s mois"%(str_age)
        # no nom sex dob age mere sms numero pb poids oedems depistage consulter
            pdfrpt.setTableData(queryset, fields, subtitle, [0.2*inch, 1.5*inch,0.3*inch,0.7*inch, 0.3*inch,1.5*inch, 0.5*inch, 0.7*inch,0.5*inch, 0.5*inch,0.5*inch,1.5*inch,1*inch])
            filename="Listing_Enfant_"+ datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
    
            pdfrpt.setFilename(filename)
    
        
    return pdfrpt.render()

#Fin Ajout new
@login_required
def malnutrition_screening(request, object_id=None, per_page="0", rformat="pdf"):
    
    ''' Malnutrition Screening Form Originally for SN CC '''
    
    pdfrpt = []
    pdfrpt = PDFReport()
    
    #fourteen_days = timedelta(days=30)
    today = datetime.now()
    
    #duration_start = day_start(today - fourteen_days)
    #duration_end = today
    
    #pdfrpt.setTitle("ChildCount Kenya: @Risk Malnutrition Cases from %s to %s"%(duration_start.date(), duration_end.date()))
    pdfrpt.setTitle("ChildCount Senegal: Formulaire de Depistage")
    #pdfrpt.setRowsPerPage(66)
    pdfrpt.setNumOfColumns(1)
    pdfrpt.setLandscape(True)
    
    if object_id is None and not request.POST:
        sites = Location.objects.filter(type__name="Site")
        for site in sites:
            queryset, fields = ReportAllPatients.malnutrition_screening_info(site)
            subtitle = "%s: Registre des Enfants pour: "%(site.name)
            pdfrpt.setTableData(queryset, fields, subtitle, [0.2*inch, 0.4*inch,1*inch,0.3*inch, .3*inch,.8*inch, .5*inch, .2*inch,0.5*inch, 0.8*inch,1*inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("malnutrition_at_risk")
    else:        
        if request.POST['zone']:
            site_id = request.POST['zone']
            site = Location.objects.get(id=site_id)
            queryset, fields = ReportAllPatients.malnutrition_screening_info(site)
        
            subtitle = "Registre des Enfants pour: %s"%(site.name)
        # no nom sex dob age mere sms numero pb poids oedems ddepistage consulter
            pdfrpt.setTableData(queryset, fields, subtitle, [0.4*inch, 1.5*inch,0.4*inch,0.7*inch, 0.3*inch,1.5*inch, 1.0*inch,0.5*inch, 0.7*inch,0.5*inch, 0.7*inch,0.7*inch,1.0*inch,0.5*inch])
            filename="formulaire_de_depistage"+ datetime.today().strftime("%Y_%m_%d_%H_%M_%S")

            pdfrpt.setFilename(filename)
    
    return pdfrpt.render()

def handle_csv(request, queryset, fields, file_name):
    
    '''Generate a csv file
    
    queryset  -    data
    fields    -    the titles for the data
    file_name -    file name
    
    '''
    
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False
    for row in queryset:
        ctx = Context({"object": row })
        if not header:
            csvio.writerow([f["name"] for f in fields])
            header = True
        values = [Template(h["bit"]).render(ctx) for h in fields]
        csvio.writerow(values)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = "attachment; filename=%s" % file_name
    response.write(output.getvalue())
    return response


@login_required
def report_view(request, report_name, object_id=None):
    
    '''view a specified report
    
    report_name - the name of the report
    object_id - a query to be applied to the specified report
    
    returns csv|pdf stream of the report
    '''
    
    part = report_name.partition('_')
    if part.__len__() == 3:
        report_name = part[0]
        format  = part[2]
    else:
        format  = 'csv'
        
    if report_name  == 'monitoring':
        month   = datetime(int(object_id[2:6]), int(object_id[:2]), 1)
        filename    = "%(report)s_%(date)s.%(ext)s" % {'report':report_name, 'date': month.strftime("%B-%Y"), 'ext':format}
        return report_monitoring_csv(request, object_id, filename)
    if report_name == 'measlessummary':
        return measles_mini_summary_csv(request, "measles_summary.csv")
    if report_name == "all-patient":        
        filename    = "%(report)s_%(date)s.%(ext)s" % {'report':report_name, 'date': datetime.today().strftime("%Y-%m-%d"), 'ext':format}
        if object_id == "1":
            return all_providers_list_pdf(request, filename,True)
        else:
            return all_providers_list_pdf(request, filename)
    if report_name == "chwstatus":
        return chwstatus_pdf(request)
    queryset, fields = build_report(report_name, object_id)
    filename    = "%(report)s_%(date)s.%(ext)s" % {'report':report_name, 'date': datetime.today().strftime("%Y-%m-%d"), 'ext':format}
    
    return eval("handle_%s" % format)(request, queryset, fields, filename)

@login_required
def malnut(request, object_id=None, per_page="0", rformat="pdf"):
    
    '''List @Risk Malnutrition Cases per clinic '''
    
    pdfrpt = PDFReport()
    
    fourteen_days = timedelta(days=30)
    today = datetime.now()
    
    duration_start = day_start(today - fourteen_days)
    duration_end = today
    
    pdfrpt.setTitle("ChildCount Kenya: @Risk Malnutrition Cases from %s to %s"%(duration_start.date(), duration_end.date()))
    #pdfrpt.setRowsPerPage(66)
    pdfrpt.setNumOfColumns(2)
    pdfrpt.setLandscape(True)
    
    if object_id is None and not request.POST:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportAllPatients.malnutrition_at_risk(duration_start, duration_end, clinic)
            c = clinic
            subtitle = "%s: @Risk Malnutrition Cases from %s to %s"%(c.name, duration_start.date(), duration_end.date())
            pdfrpt.setTableData(queryset, fields, subtitle, [0.2*inch, 0.4*inch,1*inch,0.3*inch, .3*inch,.8*inch, .5*inch, .2*inch,0.5*inch, 0.8*inch,1*inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("malnutrition_at_risk")
    else:        
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.malnutrition_at_risk(duration_start, duration_end, object_id)
        
        subtitle = "%s: @Risk Malnutrition Cases from %s to %s"%(object_id.name, duration_start.date(), duration_end.date())
        pdfrpt.setTableData(queryset, fields, subtitle, [0.2*inch, 0.4*inch,1*inch,0.3*inch, .3*inch,.8*inch, .5*inch, .2*inch,0.5*inch, 0.8*inch,1*inch])
        pdfrpt.setFilename("malnutrition_at_risk")
    
    return pdfrpt.render()

@login_required
def malaria(request, object_id=None, per_page="0", rformat="pdf"):
    
    ''' List Positive RDT Test Cases per clinic  '''
    
    pdfrpt = PDFReport()
    
    fourteen_days = timedelta(days=14)
    today = datetime.now()
    
    duration_start = day_start(today - fourteen_days)
    duration_end = today
    
    pdfrpt.setTitle("ChildCount Kenya: Positive RDT Cases from %s to %s"%(duration_start.date(), duration_end.date()))
    pdfrpt.setRowsPerPage(66)
    
    if object_id is None and not request.POST:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportAllPatients.malaria_at_risk(duration_start, duration_end, clinic)
            c = clinic
            subtitle = "%s: Positive RDT Cases from %s to %s"%(c.name, duration_start.date(), duration_end.date())
            pdfrpt.setTableData(queryset, fields, subtitle, [0.3*inch, 0.4*inch,1*inch,0.4*inch, .4*inch,.4*inch,0.5*inch, .8*inch, .4*inch,1*inch,1*inch,1.4*inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("malaria_cases")
    else:        
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.malaria_at_risk(duration_start, duration_end, object_id)
        
        subtitle = "%s: Positive RDT Cases from %s to %s"%(object_id.name, duration_start.date(), duration_end.date())
        pdfrpt.setTableData(queryset, fields, subtitle, [0.3*inch, 0.4*inch,1*inch,0.4*inch, .4*inch,.4*inch,0.5*inch, .8*inch, .4*inch,1*inch,1*inch,1.4*inch])
        pdfrpt.setFilename("malaria_cases")
    
    return pdfrpt.render()

def report_monitoring_csv(request, object_id, file_name):
    
    '''Generate a monthly monitoring report in csf format
    
    object_id - a date string e.g 112009 - November, 2009
    file_name - csv filename
    
    return csv stream
    '''
    
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False
    
    # parse parameter
    month   = datetime(int(object_id[2:6]), int(object_id[:2]), 1)
    
    # Header Line (days of month)
    eom = month_end(month)
    days= range(-1, eom.day + 1)
    days.remove(0)
    gdays   = days # store that good list
    csvio.writerow([d.__str__().replace("-1", month.strftime("%B")) for d in days])
    
    # Initialize Rows
    sms_num     = ["# SMS Sent"]
    sms_process = ["Processed"]
    sms_refused = ["Refused"]
    
    chw_tot     = ["Total CHWs in System"]
    chw_reg     = ["New CHWs Registered"]
    chw_reg_err = ["Failed Registration"]

    chw_on      = ["Active CHWS"]

    patient_reg = ["New Patients Registered"]
    patient_reg_err = ["Registration Failed"]

    malaria_tot = ["Total Malaria Reports"]
    malaria_err = ["Malaria Reports (Failed)"]

    malaria_pos = ["Malaria Tests Positive"]
    bednet_y_pos= ["Bednet Yes"]
    bednet_n_pos= ["Bednet No"]
    malaria_neg = ["Malaria Tests False"]
    bednet_y_neg= ["Bednet Yes"]
    bednet_n_neg= ["Bednet No"]

    malnut_tot  = ["Total Malnutrition Reports"]
    malnut_err  = ["Malnutrition Reports (Failed)"]

    samp_tot     = ["Total SAM+"]
    sam_tot     = ["Total SAM"]
    mam_tot     = ["Total MAM"]

    samp_new    = ["New SAM+"]
    sam_new     = ["New SAM"]
    mam_new     = ["New MAM"]

    user_msg    = ["User Messaging"]
    
    blank       = []

    # List all rows    
    rows    = [blank, sms_num, sms_process, sms_refused, blank, chw_tot, chw_reg, chw_reg_err, blank,
    chw_on, blank, patient_reg, patient_reg_err, blank, malaria_tot, malaria_err, blank, 
    malaria_pos, bednet_y_pos, bednet_n_pos, malaria_neg, bednet_y_neg, bednet_n_neg, blank,
    malnut_tot, malnut_err, blank, samp_tot, sam_tot, mam_tot, blank, samp_new, sam_new, mam_new, blank, user_msg]
    
    # Loop on days
    for d in gdays:
        if d == -1: continue
        ref_date    = datetime(month.year, month.month, d)
        morning     = day_start(ref_date)
        evening     = day_end(ref_date)
        
        # Number of SMS Sent
        sms_num.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening).count())
        
        # Number of SMS Processed
        sms_process.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, was_handled=True).count())
        
        # Number of SMS Refused
        sms_refused.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, was_handled=False).count())
        
        # Total # of CHW in System
        chwrole = Role.objects.get(code="chw")
        
        chw_tot.append(Reporter.objects.filter(role=chwrole).count())
        
        # New Registered CHW
        #chw_reg.append(Provider.objects.filter(role=Provider.CHW_ROLE,user__in=User.objects.filter(date_joined__gte=morning, date_joined__lte=evening)).count())
        chw_reg.append(0)
        # Failed CHW Registration
        chw_reg_err.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="provider_registered").count() - EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="confirmed_join").count())
        
        # Active CHWs
        a = Case.objects.filter(created_at__gte=morning, created_at__lte=evening)
        a.query.group_by = ['childcount_case.reporter_id']
        chw_on.append(a.__len__())
        
        # New Patient Registered
        patient_reg.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="patient_created").count())
        
        # Failed Patient Registration
        patient_reg_err.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__istartswith="new").count() + MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__istartswith="birth").count() - patient_reg[-1])
        
        # Total Malaria Reports
        malaria_tot.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="mrdt_taken").count())
        
        # Failed Malaria Reports
        malaria_err.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__istartswith="mrdt").count() - malaria_tot[-1])
        
        # Malaria Test Positive
        malaria_pos.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=True).count())
        
        # Malaria Positive with Bednets
        bednet_y_pos.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=True, bednet=True).count())
        
        # Malaria Positive without Bednets
        bednet_n_pos.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=True, bednet=False).count())
        
        # Malaria Test Negative
        malaria_neg.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=False).count())
        
        # Malaria Negative with Bednets
        bednet_y_neg.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=False, bednet=True).count())
        
        # Malaria Negative without Bednets
        bednet_n_neg.append(ReportMalaria.objects.filter(entered_at__gte=morning, entered_at__lte=evening, result=False, bednet=False).count())
        
        # Total Malnutrition Reports
        malnut_tot.append(EventLog.objects.filter(created_at__gte=morning, created_at__lte=evening, message="muac_taken").count())
        
        # Failed Malnutrition Reports
        malnut_err.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__istartswith="muac").count() - malnut_tot[-1])
        
        # Total SAM+
        samp_tot.append(ReportMalnutrition.objects.filter(entered_at__lte=evening, status=ReportMalnutrition.SEVERE_COMP_STATUS).count())
        
        # Total SAM
        sam_tot.append(ReportMalnutrition.objects.filter(entered_at__lte=evening, status=ReportMalnutrition.SEVERE_STATUS).count())
        
        # Total MAM
        mam_tot.append(ReportMalnutrition.objects.filter(entered_at__lte=evening, status=ReportMalnutrition.MODERATE_STATUS).count())
        
        # New SAM+
        samp_new.append(ReportMalnutrition.objects.filter(entered_at__gte=morning, entered_at__lte=evening, status=ReportMalnutrition.SEVERE_COMP_STATUS).count())
        
        # New SAM
        sam_new.append(ReportMalnutrition.objects.filter(entered_at__gte=morning, entered_at__lte=evening, status=ReportMalnutrition.SEVERE_STATUS).count())
        
        # New MAM
        mam_new.append(ReportMalnutrition.objects.filter(entered_at__gte=morning, entered_at__lte=evening, status=ReportMalnutrition.MODERATE_STATUS).count())
        
        # User Messaging
        user_msg.append(MessageLog.objects.filter(created_at__gte=morning, created_at__lte=evening, text__startswith="@").count())

    # Write rows on CSV
    for row in rows:
        csvio.writerow([cell for cell in row])
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = "attachment; filename=%s" % file_name
    response.write(output.getvalue())
    return response

def measles_mini_summary_csv(request, file_name):
    
    '''A summary of measles report per clinic in csv format'''
    
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False
    summary =  ReportCHWStatus.measles_mini_summary()
    rows = []
    row = []
    row.append("Facility")
    row.append("No. Vaccinated")
    row.append("No. Eligible")
    row.append("%")
    rows.append(row)
    for info in summary:
        info["percentage"] = round(float(float(info["vaccinated_cases"])/float(info["eligible_cases"]))*100, 2) 
        
        row = []
        row.append(u"%(clinic)s"%info)
        row.append(u"%(vaccinated_cases)s"%info)
        row.append(u"%(eligible_cases)s"%info)
        row.append(u"%(percentage)s%%"%info)
        rows.append(row)
    # Write rows on CSV
    for row in rows:
        csvio.writerow([cell for cell in row])    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = "attachment; filename=%s" % file_name
    response.write(output.getvalue())
    return response

@login_required
def measles(request, object_id=None, per_page="0", rformat="pdf"):
    
    '''List of Cases/Children Eligible for measles not yet vaccinated'''
    
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(False)
    #pdfrpt.setTitle("RapidResponse MVP Kenya: Cases Reports by CHW")
    pdfrpt.setTitle("Measles Campaign")
    if object_id is None:        
        if request.POST and request.POST['zone']:            
            reporters = Case.objects.filter(location=request.POST['zone']).values('reporter', 'location').distinct()
            per_page = "1"
        else:
            reporters = Reporter.objects.order_by("location").all()
        for reporter in reporters:
            queryset, fields = ReportAllPatients.measles_by_provider(reporter)
            if queryset:
                title = reporter.location.name + ": "+ reporter.full_name()+" (sms format: `MEASLES +PID +PID +PID`)"
                pdfrpt.setTableData(queryset, fields, title)
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
                    pdfrpt.setFilename("report_per_page")
    else:        
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        reporter = Reporter.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.measles_by_provider(reporter)
        if queryset:
            title = reporter.full_name() + " (sms format: `MEASLES +PID +PID +PID`)"
            if rformat == "csv" or (request.POST and request.POST["format"].lower() == "csv"):
                file_name = reporter.full_name() + ".csv"
                file_name = file_name.replace(" ","_").replace("'","")
                return handle_csv(request, queryset, fields, file_name)
            
            pdfrpt.setTableData(queryset, fields, title)
    
    return pdfrpt.render()
