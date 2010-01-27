#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Report Views

header - Creates a reportlab PDF element and adds it to the global Elements
    list
p - Create a text Paragraph using  ParaStyle
pre - Create a text Preformatted Paragraph using  PreStyle
reports - Lists Report links that can be generated in childcount
last_30_days - A pdf report of chw perfomance within the last 30 days
muac_summary - A pdf report of chw perfomance within the last 30 days
measles_summary - A summary of measles report per clinic - pdf formart
patients_by_chw - List of Cases/Patient per CHW
patients_by_age - Children Screening per age for SN CC
malnutrition_screening - Malnutrition Screening Form Originally for SN CC
handle_csv - Generate a csv file
report_view - view a specified report
malnut - List @Risk Malnutrition Cases per clinic
malaria - List Positive RDT Test Cases per clinic
report_monitoring_csv - Generate a monthly monitoring report in csv format
measles_mini_summary_csv - A summary of measles report per clinic in csv format
measles - List of Cases/Children Eligible for measles not yet vaccinated
'''

from datetime import date, datetime, timedelta
import csv
import StringIO

from django.template import Template, Context
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from rapidsms.webui.utils import render_to_response

from locations.models import Location
from reporters.models import Reporter, Role

from childcount.utils import day_end, day_start, month_end, next_month
from childcount.shortcuts import login_required
from childcount.models.logs import MessageLog, EventLog
from childcount.models.general import Case
from childcount.models.reports import ReportCHWStatus, ReportAllPatients
from childcount.models.config import Configuration as Cfg
from muac.models import ReportMalnutrition
from mrdt.models import ReportMalaria

from libreport.pdfreport import PDFReport

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet

from childcount.forms.general import Enfant

styles = getSampleStyleSheet()
Elements = []

HeaderStyle = styles["Heading1"] # XXXX


def header(txt, style=HeaderStyle, klass=Paragraph, sep=0.3):
    '''Creates a reportlab PDF element and adds it to the global Elements list

    style - can be a HeaderStyle, a ParaStyle or a custom style,
     default HeaderStyle
    klass - the reportlab Class to be called, default Paragraph
    sep    - space separator height
    '''
    s = Spacer(0.2 * inch, sep * inch)
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
    s = Spacer(0.1 * inch, 0.1 * inch)
    Elements.append(s)
    p = Preformatted(txt, PreStyle)
    Elements.append(p)

app = {}
app['name'] = "ChildCount:Health"


@login_required
def reports(request):
    '''Lists Report links that can be generated in childcount'''
    template_name = "childcount/reports/reports.html"

    clinics = Location.objects.filter(type__name="Site")

    zones = Case.objects.order_by("location").\
                values('location', 'location__name').distinct()
    p = Case.objects.order_by("location").values('reporter', \
                'reporter__first_name', 'reporter__last_name', 'location').\
                distinct()
    providers = []
    for provider in p:
        tmp = {}
        tmp['id'] = provider['reporter']
        tmp['name'] = provider['reporter__last_name'] + " " \
                 + provider['reporter__first_name']
        tmp['zone'] = provider['location']
        providers.append(tmp)

    now = datetime.today()
    first = Case.objects.order_by('created_at')[:1][0]
    date = first.created_at

    months = []
    tab_mois = range(1, 61, 1)
    while ((now - date).days > 0):
        months.append({'id': date.strftime("%m%Y"), 'label': \
                       date.strftime("%B %Y"), 'date': date})
        date = next_month(date)

    context = {
        "app": app,
        "clinics": clinics,
        "providers": providers,
        "zones": zones,
        "months": months,
        "lesmois": tab_mois}
    return render_to_response(request, template_name, context)


@login_required
def last_30_days(request, object_id=None, per_page="0", rformat="pdf", d="30"):
    '''A pdf report of chw perfomance within the last 30 days'''
    pdfrpt = PDFReport()
    pdfrpt.enableFooter(True)

    d = int(d)
    thirty_days = timedelta(days=d)
    ninty_days = timedelta(days=90)
    today = date.today()

    duration_start = today - thirty_days
    muac_duration_start = today - ninty_days
    duration_end = today

    pdfrpt.setTitle(_(Cfg.get("app_name") + ": CHW 30 Day Performance Report,"\
                    " from %(start_date)s " \
            "to %(end_date)s" % ({'start_date': duration_start, \
                                  'end_date': duration_end})))
    title = _("CHW 30 Day Performance Report, from %(start_date)s " \
            "to %(end_date)s" % {'start_date': duration_start, \
                                  'end_date': duration_end})

    if object_id is None:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.\
                get_providers_by_clinic(duration_start, duration_end, \
                                        muac_duration_start, clinic)
            stitle = "%s: %s" % (clinic.name, title)
            pdfrpt.setTableData(queryset, fields, stitle, \
                [0.3 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, .8 * inch, \
                 .8 * inch, 0.8 * inch, 1 * inch, 1 * inch, 1 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.\
                get_providers_by_clinic(duration_start, duration_end, \
                                        muac_duration_start, object_id)
        stitle = "%s: %s" % (object_id.name, title)
        if rformat == "csv" or (request.POST \
                                and request.POST["format"].lower() == "csv"):
            file_name = object_id.name + ".csv"
            file_name = file_name.replace(" ", "_").replace("'", "")
            return handle_csv(request, queryset, fields, file_name)

        pdfrpt.setTableData(queryset, fields, stitle)

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

    duration_str = _("CMAM Summary from %(start_date)s to %(end_date)s") % \
        {'start_date': duration_start.strftime("%d %B, %Y"), \
         'end_date': today.strftime("%d %B, %Y")}

    pdfrpt.setTitle(Cfg.get("app_name") + _(": CMAM Summary from %(start_date)s to %(end_date)s") % \
                    {'start_date': duration_start, 'end_date': duration_end})

    if object_id is None:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.muac_summary(duration_start, \
                                                duration_end, clinic)
            title = "%s : %s" % (clinic.name, duration_str)
            pdfrpt.setTableData(queryset, fields, title, \
                        [0.3 * inch, 1 * inch, 0.8 * inch, 0.8 * inch, \
                         .8 * inch, .8 * inch, 0.8 * inch, 1 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.muac_summary(duration_start, \
                                                duration_end, object_id)
        c = object_id

        if rformat == "csv" or (request.POST and \
                                request.POST["format"].lower() == "csv"):
            file_name = c.name + ".csv"
            file_name = file_name.replace(" ", "_").replace("'", "")
            return handle_csv(request, queryset, fields, file_name)
        title = "%s : %s" % (c.name, duration_str)
        pdfrpt.setTableData(queryset, fields, title)

    return pdfrpt.render()


@login_required
def measles_summary(request, object_id=None, per_page="0", \
                    rformat="pdf", d="30"):
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

    pdfrpt.setTitle(_("Measles Campaign Summary"))
    if object_id is None:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.\
                measles_summary(duration_start, duration_end, \
                                muac_duration_start, clinic)
            pdfrpt.setTableData(queryset, fields, clinic)
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/report_per_page")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
        clinic = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.\
            measles_summary(duration_start, duration_end, \
                            muac_duration_start, clinic)

        if rformat == "csv" or (request.POST \
                                and request.POST["format"].lower() == "csv"):
            file_name = clinic + ".csv"
            file_name = file_name.replace(" ", "_").replace("'", "")
            return handle_csv(request, queryset, fields, file_name)

        pdfrpt.setTableData(queryset, fields, clinic)

    return pdfrpt.render()

##
@login_required
def vitamines_summary(request, object_id=None, per_page="0", \
                    rformat="pdf", d="30"):
    '''A summary of vitamines A report per Site - pdf formart'''
    pdfrpt = PDFReport()
    d = int(d)
    pdfrpt.enableFooter(True)

    thirty_days = timedelta(days=d)
    ninty_days = timedelta(days=90)
    today = date.today()

    duration_start = today - thirty_days
    muac_duration_start = today - ninty_days
    duration_end = today

    pdfrpt.setTitle(_("Vitamines Campaign Summary"))
    if object_id is None:
        clinics = Location.objects.filter(type__name="Site")
        for clinic in clinics:
            queryset, fields = ReportCHWStatus.\
                vitamines_summary(duration_start, duration_end, \
                                muac_duration_start, clinic)
            pdfrpt.setTableData(queryset, fields, clinic,\
                            [1.0* inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, \
                             1.0 * inch, 1.5 * inch, 1.0 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
            pdfrpt.setFilename("/tmp/vitamines_per_page")
    else:
        if request.POST['site']:
            object_id = request.POST['site']
        clinic = Location.objects.get(id=object_id)
        queryset, fields = ReportCHWStatus.\
            vitamines_summary(duration_start, duration_end, \
                            muac_duration_start, clinic)

        if rformat == "csv" or (request.POST \
                                and request.POST["format"].lower() == "csv"):
            file_name = clinic.name + ".csv"
            file_name = file_name.replace(" ", "_").replace("'", "")
            return handle_csv(request, queryset, fields, file_name)

        pdfrpt.setTableData(queryset, fields, clinic,\
                            [1.0* inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, \
                             1.0 * inch, 1.5 * inch, 1.0 * inch])
        if (int(per_page) == 1) is True:
            pdfrpt.setPageBreak()
        pdfrpt.setFilename("/tmp/vitamines_per_page")
    return pdfrpt.render()

##
@login_required
def patients_by_chw(request, object_id=None, per_page="0", rformat="pdf"):
    '''List of Cases/Patient per CHW'''
    today = datetime.now().strftime("%d %B,%Y")
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(True)
    pdfrpt.setPrintOnBothSides(True)
    
    pdfrpt.setTitle(_("%(app_name)s: Cases Reports by CHW as of %(date)s") % {'date': today,'app_name':Cfg.get("app_name")})
    
    pdfrpt.setNumOfColumns(2)
    #pdfrpt.setRowsPerPage(88)
    if object_id is None:
        if request.POST and request.POST['zone']:
         #   providers = Case.objects.filter(location=request.POST['zone']).\
          #      values('reporter', 'location').distinct()
            providers = Reporter.objects.filter(location=request.POST['zone'])
            #per_page = "1"
        else:
            providers = Reporter.objects.all()
         #   providers = Case.objects.order_by("location").\
         #                   values('reporter', 'location').distinct()
        
            
        for reporter in providers:
            queryset, fields = ReportAllPatients.by_provider(reporter)
            if queryset:
                cinfo = {'loc': reporter.location,
                         'lname': reporter.last_name,
                         'fname': reporter.first_name,
                         'date': today}
                c = _("%(loc)s: %(lname)s %(fname)s: %(date)s" % cinfo)
                pdfrpt.setTableData(queryset, fields, c, \
                            [0.3 * inch, 0.4 * inch, 1 * inch, 0.4 * inch, \
                             0.3 * inch, 0.8 * inch, 0.5 * inch, 1 * inch, \
                             0.8 * inch])
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/report_per_page")
    else:
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        reporter = Reporter.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.by_provider(reporter)
        if queryset:
            cinfo = {'loc': reporter.location,
                     'lname': reporter.last_name,
                     'fname': reporter.first_name,
                     'date': today}
            c = _("%(loc)s: %(lname)s %(fname)s: %(date)s" % cinfo)
            if rformat == "csv" or (request.POST \
                                and request.POST["format"].lower() == "csv"):
                file_name = reporter.last_name + ".csv"
                file_name = file_name.replace(" ", "_").replace("'", "")
                return handle_csv(request, queryset, fields, file_name)

            pdfrpt.setTableData(queryset, fields, c, \
                            [0.3 * inch, 0.4 * inch, 1 * inch, 0.4 * inch, \
                             0.3 * inch, 0.4 * inch, 0.5 * inch, 1 * inch, \
                             1 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
            pdfrpt.setFilename("/tmp/report_per_page")

    return pdfrpt.render()


@login_required
def dead_cases_report(request, rformat="pdf"):
    '''List of Cases/Patient per CHW'''
    today = datetime.now().strftime("%d %B,%Y")
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(True)
    title = _("%(app_name)s: Dead Cases report as of %(date)s" % \
               {'app_name': Cfg.get("app_name"), 'date': today})
    pdfrpt.setTitle(title)
    pdfrpt.setNumOfColumns(1)
    queryset, fields = \
        ReportAllPatients.death_report_by_provider()
    if queryset:
        pdfrpt.setTableData(queryset, fields, title, \
                    [0.3 * inch, 0.4 * inch, 1 * inch, 0.4 * inch, \
                     0.5 * inch, 0.8 * inch, 0.5 * inch, 1 * inch, \
                     0.6 * inch, 1.4 * inch, 1.5 * inch, 1 * inch, \
                     1.3 * inch, 1.2 * inch])
    pdfrpt.setFilename("/tmp/deathreport_")

    return pdfrpt.render()


@login_required
#Modification Assane new
def patients_by_age(request, object_id=None, per_page="0", rformat="pdf"):
    ''' Children Screening per age for SN CC '''
    pdfrpt = PDFReport()

    #pdfrpt.setTitle(_("ChildCount Senegal: Listing Enfant par Age"))
    pdfrpt.setTitle(_(Cfg.get("app_name") + \
                ": Listing Enfant par Age" ))
    #pdfrpt.setRowsPerPage(66)
    pdfrpt.setNumOfColumns(1)
    pdfrpt.setLandscape(True)
    pdfrpt.setFontSize(10)
    if object_id is None and not request.POST:
        age_mois = 0
        cases = Case.objects.order_by("location").distinct()
        queryset, fields = ReportAllPatients.by_age(age_mois, cases)
        subtitle = _("Registre des Enfants pour: ") #%(site.name)
        pdfrpt.setTableData(queryset, fields, subtitle, \
                    [0.2 * inch, 1.5 * inch, 0.5 * inch, 0.7 * inch, \
                     0.5 * inch, 1.5 * inch,1.0 * inch, 0.5 * inch, 0.7 * inch, \
                     0.5 * inch, 0.5 * inch, 0.7 * inch, 1.5 * inch, \
                     1 * inch])
        if (int(per_page) == 1) is True:
            pdfrpt.setPageBreak()
        pdfrpt.setFilename("/tmp/Listing_Enfant")

    else:
        cases = Case.objects.order_by("location").distinct()

        if request.POST['age']:
            age_mois = int(request.POST['age'])
            str_age = request.POST['age']

            queryset, fields = ReportAllPatients.by_age(age_mois, cases)

            subtitle = _("Registre des Enfants de : %(age)s mois" % \
                         {'age': str_age})
        # no nom sex dob age mere sms numero pb poids oedems
        #depistage consulter
            pdfrpt.setTableData(queryset, fields, subtitle, \
                        [0.2 * inch, 1.5 * inch, 0.5 * inch, 0.7 * inch, \
                         0.5 * inch, 1.5 * inch,1.0 * inch, 0.5 * inch, 0.7 * inch, \
                         0.5 * inch, 0.5 * inch, 0.7 * inch, 1.5 * inch, \
                         1 * inch])
            filename = "/tmp/Listing_Enfant_" + \
                datetime.today().strftime("%Y_%m_%d_%H_%M_%S")

            pdfrpt.setFilename(filename)

    return pdfrpt.render()


#Fin Ajout new
@login_required
def malnutrition_screening(request, object_id=None, per_page="0", \
                           rformat="pdf"):
    ''' Malnutrition Screening Form Originally for SN CC '''
    pdfrpt = []
    pdfrpt = PDFReport()

    #fourteen_days = timedelta(days=30)
    today = datetime.now()

    #duration_start = day_start(today - fourteen_days)
    #duration_end = today

    pdfrpt.setTitle("%(app_name)s: Formulaire de Depistage" % \
                   {'app_name': Cfg.get("app_name")})
    #pdfrpt.setRowsPerPage(66)
    pdfrpt.setNumOfColumns(1)
    pdfrpt.setLandscape(True)
    pdfrpt.setFontSize(10)
    if object_id is None and not request.POST:
        sites = Location.objects.filter(type__name="Site")
        for site in sites:
            queryset, fields = \
                ReportAllPatients.malnutrition_screening_info(site)
            subtitle = _("%(site_name)s: Registre des Enfants pour: " % \
                         {'site_name': site.name})
            pdfrpt.setTableData(queryset, fields, subtitle, \
                            [0.4 * inch, 1.5 * inch, 0.4 * inch, 0.5 * inch, \
                             0.5 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch, \
                             0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, \
                             0.8 * inch, 1.0 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/malnutrition_at_risk")
    else:
        if request.POST['zone']:
            site_id = request.POST['zone']
            site = Location.objects.get(id=site_id)
            queryset, fields = \
                ReportAllPatients.malnutrition_screening_info(site)

            subtitle = _("Registre des Enfants pour: %(site_name)s" % \
                         {'site_name': site.name})
        # no nom sex dob age mere sms numero pb poids oedems
        # ddepistage consulter
            pdfrpt.setTableData(queryset, fields, subtitle, \
                            [0.4 * inch, 1.5 * inch, 0.4 * inch, 0.5 * inch, \
                             0.5 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch, \
                             0.7 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch, \
                             0.8 * inch, 1.0 * inch])
            filename = "/tmp/formulaire_de_depistage" + \
                    datetime.today().strftime("%Y_%m_%d_%H_%M_%S")

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
        ctx = Context({"object": row})
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
        format = part[2]
    else:
        format = 'csv'

    if report_name == 'monitoring':
        month = datetime(int(object_id[2:6]), int(object_id[:2]), 1)
        filename = "%(report)s_%(date)s.%(ext)s" % {'report': report_name, \
                        'date': month.strftime("%B-%Y"), 'ext': format}
        return report_monitoring_csv(request, object_id, filename)
    if report_name == 'measlessummary':
        return measles_mini_summary_csv(request, "measles_summary.csv")

    '''if report_name == "all-patient":
        filename    = "%(report)s_%(date)s.%(ext)s" % \
            {'report':report_name, 'date':\
              datetime.today().strftime("%Y-%m-%d"), 'ext':format}
        if object_id == "1":
            return all_providers_list_pdf(request, filename,True)
        else:
            return all_providers_list_pdf(request, filename)
    if report_name == "chwstatus":
        return chwstatus_pdf(request)
    queryset, fields = build_report(report_name, object_id)
    filename    = " % (report)s_%(date)s.%(ext)s" % \
        {'report':report_name, 'date': \
         datetime.today().strftime("%Y-%m-%d"), 'ext':format}
    return eval("handle_%s" % format)(request, queryset, fields, filename)'''


@login_required
def malnut(request, object_id=None, per_page="0", rformat="pdf"):
    '''List @Risk Malnutrition Cases per clinic '''
    pdfrpt = PDFReport()

    fourteen_days = timedelta(days=30)
    today = datetime.now()

    duration_start = day_start(today - fourteen_days)
    duration_end = today

    pdfrpt.setTitle(_("%(app_name)s: @Risk Malnutrition Cases from"\
                     " %(start_date)s to %(end_date)s"\
                     % {'start_date': duration_start.date(),
                        'end_date': duration_end.date(),
                        'app_name': Cfg.get("app_name")}))
    #pdfrpt.setRowsPerPage(66)
    pdfrpt.setNumOfColumns(2)
    pdfrpt.setLandscape(True)

    if object_id is None and not request.POST:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = \
                ReportAllPatients.malnutrition_at_risk(duration_start, \
                                                       duration_end, clinic)
            c = clinic
            subtitle = _("%(clinic)s: @Risk Malnutrition Cases from "\
                "%(start_date)s to %(end_date)s" % \
                {'clinic': c.name, 'start_date': duration_start.date(), \
                 'end_date': duration_end.date()})
            pdfrpt.setTableData(queryset, fields, subtitle, \
                        [0.2 * inch, 0.4 * inch, 1 * inch, 0.3 * inch, \
                         .3 * inch, .8 * inch, .5 * inch, .2 * inch, \
                         0.5 * inch, 0.8 * inch, 1 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/malnutrition_at_risk")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = \
            ReportAllPatients.malnutrition_at_risk(duration_start, \
                                                   duration_end, object_id)

        subtitle = _("%(clinic)s: @Risk Malnutrition Cases from "\
                "%(start_date)s to %(end_date)s" % \
                {'clinic': object_id.name, \
                 'start_date': duration_start.date(), \
                 'end_date': duration_end.date()})
        pdfrpt.setTableData(queryset, fields, subtitle, \
                        [0.2 * inch, 0.4 * inch, 1 * inch, 0.3 * inch, \
                         .3 * inch, .8 * inch, .5 * inch, .2 * inch, \
                         0.5 * inch, 0.8 * inch, 1 * inch])
        pdfrpt.setFilename("/tmp/malnutrition_at_risk")

    return pdfrpt.render()


@login_required
def malaria(request, object_id=None, per_page="0", rformat="pdf"):
    ''' List Positive RDT Test Cases per clinic  '''
    pdfrpt = PDFReport()

    fourteen_days = timedelta(days=14)
    today = datetime.now()

    duration_start = day_start(today - fourteen_days)
    duration_end = today

    pdfrpt.setTitle(_("%(app_name)s: Positive RDT Cases from "\
                      "%(start_date)s to %(end_date)s" % \
                    {'start_date': duration_start.date(), \
                     'end_date': duration_end.date(),
                     'app_name': Cfg.get("app_name")}))
    pdfrpt.setRowsPerPage(66)

    if object_id is None and not request.POST:
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            queryset, fields = \
                ReportAllPatients.malaria_at_risk(duration_start, \
                                                  duration_end, clinic)
            c = clinic
            subtitle = _("%(clinic)s: Positive RDT Cases from "\
                "%(start_date)s to %(end_date)s" % {'clinic': c.name, \
                'start_date': duration_start.date(), \
                'end_date': duration_end.date()})

            pdfrpt.setTableData(queryset, fields, subtitle, \
                        [0.3 * inch, 0.4 * inch, 1 * inch, 0.4 * inch, \
                         .4 * inch, .4 * inch, 0.5 * inch, .8 * inch, \
                         .4 * inch, 1 * inch, 1 * inch, 1.4 * inch])
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/malaria_cases")
    else:
        if request.POST['clinic']:
            object_id = request.POST['clinic']
            object_id = Location.objects.get(id=object_id)
        queryset, fields = \
            ReportAllPatients.malaria_at_risk(duration_start, \
                                              duration_end, object_id)

        subtitle = _("%(clinic)s: Positive RDT Cases from "\
            "%(start_date)s to %(end_date)s" % {'clinic': object_id.name, \
            'start_date': duration_start.date(), \
            'end_date': duration_end.date()})
        pdfrpt.setTableData(queryset, fields, subtitle, \
                    [0.3 * inch, 0.4 * inch, 1 * inch, 0.4 * inch, \
                     .4 * inch, .4 * inch, 0.5 * inch, .8 * inch, \
                     .4 * inch, 1 * inch, 1 * inch, 1.4 * inch])
        pdfrpt.setFilename("/tmp/malaria_cases")

    return pdfrpt.render()


def report_monitoring_csv(request, object_id, file_name):
    '''Generate a monthly monitoring report in csv format

    object_id - a date string e.g 112009 - November, 2009
    file_name - csv filename

    return csv stream
    '''
    output = StringIO.StringIO()
    csvio = csv.writer(output)
    header = False

    # parse parameter
    month = datetime(int(object_id[2:6]), int(object_id[:2]), 1)

    # Header Line (days of month)
    eom = month_end(month)
    days = range(-1, eom.day + 1)
    days.remove(0)
    # store that good list
    gdays = days
    csvio.writerow([d.__str__().replace("-1", \
                            month.strftime("%B")) for d in days])

    # Initialize Rows
    sms_num = ["# SMS Sent"]
    sms_process = ["Processed"]
    sms_refused = ["Refused"]

    chw_tot = ["Total CHWs in System"]
    chw_reg = ["New CHWs Registered"]
    chw_reg_err = ["Failed Registration"]

    chw_on = ["Active CHWS"]

    patient_reg = ["New Patients Registered"]
    patient_reg_err = ["Registration Failed"]

    malaria_tot = ["Total Malaria Reports"]
    malaria_err = ["Malaria Reports (Failed)"]

    malaria_pos = ["Malaria Tests Positive"]
    bednet_y_pos = ["Bednet Yes"]
    bednet_n_pos = ["Bednet No"]
    malaria_neg = ["Malaria Tests False"]
    bednet_y_neg = ["Bednet Yes"]
    bednet_n_neg = ["Bednet No"]

    malnut_tot = ["Total Malnutrition Reports"]
    malnut_err = ["Malnutrition Reports (Failed)"]

    samp_tot = ["Total SAM+"]
    sam_tot = ["Total SAM"]
    mam_tot = ["Total MAM"]

    samp_new = ["New SAM+"]
    sam_new = ["New SAM"]
    mam_new = ["New MAM"]

    user_msg = ["User Messaging"]

    blank = []

    # List all rows
    rows = [blank, sms_num, sms_process, sms_refused, blank, chw_tot, \
               chw_reg, chw_reg_err, blank, \
               chw_on, blank, patient_reg, patient_reg_err, blank, \
               malaria_tot, malaria_err, blank, malaria_pos, bednet_y_pos, \
               bednet_n_pos, malaria_neg, bednet_y_neg, bednet_n_neg, blank, \
               malnut_tot, malnut_err, blank, samp_tot, sam_tot, mam_tot, \
               blank, samp_new, sam_new, mam_new, blank, user_msg]

    # Loop on days
    for d in gdays:
        if d == -1:
            continue
        ref_date = datetime(month.year, month.month, d)
        morning = day_start(ref_date)
        evening = day_end(ref_date)

        # Number of SMS Sent
        sms_num.append(MessageLog.objects.filter(created_at__gte=morning, \
                                        created_at__lte=evening).count())

        # Number of SMS Processed
        sms_process.append(MessageLog.objects.filter(created_at__gte=morning, \
                        created_at__lte=evening, was_handled=True).count())

        # Number of SMS Refused
        sms_refused.append(MessageLog.objects.filter(created_at__gte=morning, \
                        created_at__lte=evening, was_handled=False).count())

        # Total # of CHW in System
        chwrole = Role.objects.get(code="chw")
        chw_tot.append(Reporter.objects.filter(role=chwrole).count())

        # New Registered CHW
        #chw_reg.append(Provider.objects.filter(role=Provider.CHW_ROLE, \
        #user__in=User.objects.filter(date_joined__gte=morning, \
        #date_joined__lte=evening)).count())
        chw_reg.append(0)
        # Failed CHW Registration
        chw_reg_err.append(EventLog.objects.filter(created_at__gte=morning, \
            created_at__lte=evening, message="provider_registered").count() - \
            EventLog.objects.filter(created_at__gte=morning, \
            created_at__lte=evening, message="confirmed_join").count())

        # Active CHWs
        a = Case.objects.filter(created_at__gte=morning, \
                                created_at__lte=evening)
        a.query.group_by = ['childcount_case.reporter_id']
        chw_on.append(a.__len__())

        # New Patient Registered
        patient_reg.append(EventLog.objects.filter(created_at__gte=morning, \
                created_at__lte=evening, message="patient_created").count())

        # Failed Patient Registration
        patient_reg_err.append(MessageLog.objects.filter(\
                created_at__gte=morning, created_at__lte=evening, \
                text__istartswith="new").count() + \
                MessageLog.objects.filter(created_at__gte=morning, \
                created_at__lte=evening, text__istartswith="birth").\
                count() - patient_reg[-1])

        # Total Malaria Reports
        malaria_tot.append(EventLog.objects.filter(created_at__gte=morning, \
                created_at__lte=evening, message="mrdt_taken").count())

        # Failed Malaria Reports
        malaria_err.append(MessageLog.objects.filter(created_at__gte=morning, \
            created_at__lte=evening, text__istartswith="mrdt").count() - \
            malaria_tot[-1])

        # Malaria Test Positive
        malaria_pos.append(ReportMalaria.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
             result=True).count())

        # Malaria Positive with Bednets
        bednet_y_pos.append(ReportMalaria.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, result=True, \
             bednet=True).count())

        # Malaria Positive without Bednets
        bednet_n_pos.append(ReportMalaria.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, result=True, \
             bednet=False).count())

        # Malaria Test Negative
        malaria_neg.append(ReportMalaria.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
             result=False).count())

        # Malaria Negative with Bednets
        bednet_y_neg.append(ReportMalaria.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
            result=False, bednet=True).count())

        # Malaria Negative without Bednets
        bednet_n_neg.append(ReportMalaria.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
            result=False, bednet=False).count())

        # Total Malnutrition Reports
        malnut_tot.append(EventLog.objects.filter(created_at__gte=morning, \
                    created_at__lte=evening, message="muac_taken").count())

        # Failed Malnutrition Reports
        malnut_err.append(MessageLog.objects.filter(created_at__gte=morning, \
            created_at__lte=evening, text__istartswith="muac").count() - \
            malnut_tot[-1])

        # Total SAM+
        samp_tot.append(ReportMalnutrition.objects.filter(\
            entered_at__lte=evening, \
             status=ReportMalnutrition.SEVERE_COMP_STATUS).count())

        # Total SAM
        sam_tot.append(ReportMalnutrition.objects.filter(\
            entered_at__lte=evening, \
             status=ReportMalnutrition.SEVERE_STATUS).count())

        # Total MAM
        mam_tot.append(ReportMalnutrition.objects.filter(\
            entered_at__lte=evening, \
             status=ReportMalnutrition.MODERATE_STATUS).count())

        # New SAM+
        samp_new.append(ReportMalnutrition.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
             status=ReportMalnutrition.SEVERE_COMP_STATUS).count())

        # New SAM
        sam_new.append(ReportMalnutrition.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
             status=ReportMalnutrition.SEVERE_STATUS).count())

        # New MAM
        mam_new.append(ReportMalnutrition.objects.filter(\
            entered_at__gte=morning, entered_at__lte=evening, \
             status=ReportMalnutrition.MODERATE_STATUS).count())

        # User Messaging
        user_msg.append(MessageLog.objects.filter(created_at__gte=morning, \
                created_at__lte=evening, text__startswith="@").count())

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
    summary = ReportCHWStatus.measles_mini_summary()
    rows = []
    row = []
    row.append(_("Facility"))
    row.append(_("No. Vaccinated"))
    row.append(_("No. Eligible"))
    row.append("%")
    rows.append(row)
    for info in summary:
        info["percentage"] = round(float(float(info["vaccinated_cases"]) / \
                                float(info["eligible_cases"])) * 100, 2)

        row = []
        row.append(u"%(clinic)s" % info)
        row.append(u"%(vaccinated_cases)s" % info)
        row.append(u"%(eligible_cases)s" % info)
        row.append(u"%(percentage)s%%" % info)
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
    pdfrpt.setTitle(_("Measles Campaign"))
    if object_id is None:
        if request.POST and request.POST['zone']:
            reporters = Case.objects.filter(location=request.POST['zone']).\
                values('reporter', 'location').distinct()
            per_page = "1"
        else:
            reporters = Reporter.objects.order_by("location").all()
        for reporter in reporters:
            queryset, fields = ReportAllPatients.measles_by_provider(reporter)
            if queryset:
                title = reporter.location.name + ": " + \
                    reporter.full_name() + \
                    " (sms format: `MEASLES +PID +PID +PID`)"
                pdfrpt.setTableData(queryset, fields, title)
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
                pdfrpt.setFilename("/tmp/report_per_page")
    else:
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        reporter = Reporter.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.measles_by_provider(reporter)
        if queryset:
            title = reporter.full_name() + \
            " (sms format: `MEASLES +PID +PID +PID`)"
            if rformat == "csv" or (request.POST \
                                and request.POST["format"].lower() == "csv"):
                file_name = reporter.full_name() + ".csv"
                file_name = file_name.replace(" ", "_").replace("'", "")
                return handle_csv(request, queryset, fields, file_name)

            pdfrpt.setTableData(queryset, fields, title)

    return pdfrpt.render()


@login_required
def vitamines(request, object_id=None, per_page="0", rformat="pdf"):
    '''List of Cases/Children Eligible for vitamines not yet vaccinated'''
    has_data=0
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(False)
    #pdfrpt.setTitle("RapidResponse MVP Kenya: Cases Reports by CHW")
    pdfrpt.setTitle(_("Vitamines A Campaign"))
    if object_id is None:
        if request.POST and request.POST['site']:
            id_loc=request.POST['site']
            loc=Location.objects.get(id=id_loc)
            
            #reporters = Case.objects.filter(location=loc).\
            #    values('reporter', 'location').distinct()
            reporters = Reporter.objects.filter(location=loc)
            
            per_page = "1"
        else:
            reporters = Reporter.objects.all()
        
        for reporter in reporters:
            
            queryset, fields = ReportAllPatients.vitamines_by_provider(reporter)
            if queryset:
                
                title = reporter.location.name + ": " + \
                    reporter.full_name() + \
                    " (sms format: `VITA +PID +PID +PID`)"
                pdfrpt.setTableData(queryset, fields, title)
                if (int(per_page) == 1) is True:
                    pdfrpt.setPageBreak()
        pdfrpt.setFilename("/tmp/report_per_page")
        
    else:
        if request.POST and request.POST['provider']:
            object_id = request.POST['provider']
        
        reporter = Reporter.objects.get(id=object_id)
        queryset, fields = ReportAllPatients.vitamines_by_provider(reporter)
        if queryset:
            
            title = reporter.full_name() + \
            " (sms format: `VITA +PID +PID +PID`)"
            if rformat == "csv" or (request.POST \
                                and request.POST["format"].lower() == "csv"):
                file_name = reporter.full_name() + ".csv"
                file_name =file_name.replace(" ", "_").replace("'", "")
                return handle_csv(request, queryset, fields, file_name)

            pdfrpt.setTableData(queryset, fields, title)
            if (int(per_page) == 1) is True:
                pdfrpt.setPageBreak()
        pdfrpt.setFilename("/tmp/report_per_page")

    return pdfrpt.render()

@login_required
def childcount(request):
    template_name = "childcount/reports/childcount.html"

    return render_to_response(request, template_name)


@login_required
def saisie(request):
    template_name = "childcount/formulaire/saisie.html"


    if request.method == 'POST': # If the form has been submitted...
        form = Enfant(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            prenom = form.cleaned_data['first_name']

            enfant = form.save(commit=False)
            enfant.title = prenom
            enfant.save()

        last_ten = Case.objects.order_by('-created_at')[:10]
        form = Enfant()
    #return HttpResponseRedirect('childcount/saisie') # Redirect after POST
    else:
        last_ten = Case.objects.order_by('-created_at')[:10]
        form = Enfant() # An unbound form

    return render_to_response(request, template_name, {
       'form': form,
       'last_ten': last_ten,
    })


@login_required
def listeEnfant(request):
    template_name = "childcount/formulaire/Affiche_Enfant.html"
    if not request.POST:
        lalocation = None
        lereporter = None
        xaleyi = Case.objects.all()
        locations = Location.objects.all()
        reporters = Reporter.objects.all()
    else:
        locations = Location.objects.all()
        reporters = Reporter.objects.all()
        if (request.POST['location'] == "-1" \
            and request.POST['reporter'] == "-1"):
                    lalocation = None
                    lereporter = None
                    xaleyi = Case.objects.all()
        elif request.POST['location'] <> "-1" \
            and request.POST['reporter'] == "-1":
                    lalocation = Location.objects\
                        .get(id=request.POST['location'])
                    lereporter = None
                    xaleyi = Case.objects.filter(location=lalocation)
        elif request.POST['location'] == "-1" \
            and request.POST['reporter'] <> "-1":
                    lereporter = Reporter.objects\
                        .get(id=request.POST['reporter'])
                    lalocation = None
                    xaleyi = Case.objects.filter(reporter=lereporter)
        else:
            lalocation = Location.objects.get(id=request.POST['location'])
            lereporter = Reporter.objects.get(id=request.POST['reporter'])
            xaleyi = Case.objects.\
                filter(location=lalocation, reporter=lereporter)
    return render_to_response(request, template_name, {
       'xaleyi': xaleyi,
       'all_reporters': reporters,
       'all_locations': locations,
       'lereporter': lereporter,
       'lalocation': lalocation})


@login_required
def afficheEnfant(request, xaley_id=None):
    template_name = "childcount/formulaire/ListeEnfant.html"

    SEXE = [("M", 'Male'), ('F', 'Female')]
    STATUS = [(-1, 'Dead'), (0, 'Relocated'), (1, 'Alive')]

    xaleybi = Case.objects.get(id=xaley_id)

    lalocation = xaleybi.location
    lereporter = xaleybi.reporter

    xaleyi = Case.objects.filter(location=lalocation, reporter=lereporter)

    locations = Location.objects.all()
    reporters = Reporter.objects.all()
    return render_to_response(request, template_name, {
       'xaleybi': xaleybi,
       'xaleyi': xaleyi,
       'all_reporters': reporters,
       'all_locations': locations,
       'sexe': SEXE,
       'status': STATUS,
       'lereporter': lereporter,
       'lalocation': lalocation})


@login_required
def modifyEnfant(request):
    template_name = "childcount/formulaire/ListeEnfant.html"

    SEXE = [('M', 'Male'), ('F', 'Female')]
    STATUS = [('-1', 'Dead'), ('0', 'Relocated'), ('1', 'Alive')]

    case_id = request.POST['case_id']
    enfant = Case.objects.get(id=case_id)
    enfant.first_name = request.POST['first_name']
    enfant.last_name = request.POST['last_name']
    enfant.gender = request.POST['gender']
    enfant.dob = request.POST['dob']
    enfant.guardian = request.POST['guardian']
    enfant.mobile = request.POST['mobile']
    enfant.guardian = request.POST['guardian']
    enfant.status = request.POST['status']
    lereporter = Reporter.objects.get(id=request.POST['reporters'])
    lalocation = Location.objects.get(id=request.POST['locations'])

    enfant.reporter = lereporter
    enfant.location = lalocation

    #enfant.reporter.id=request.POST['reporters']
    #enfant.location.id=request.POST['locations']

    enfant.save()
    xaleyi = Case.objects.filter(location=lalocation, reporter=lereporter)
    locations = Location.objects.all()
    reporters = Reporter.objects.all()
    return render_to_response(request, template_name, {
       'xaleybi': enfant,
       'xaleyi': xaleyi,
       'all_reporters': reporters,
       'all_locations': locations,
       'sexe': SEXE,
       'status': STATUS,
       'lereporter': lereporter,
       'lalocation': lalocation})
