#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response

from django.http import HttpResponse

from datetime import datetime
from deathform.models.general import ReportDeath
import re

from muac.models import ReportMalnutrition
from mrdt.models import ReportMalaria
from childcount.models.general import Case
from measles.models import ReportMeasles
from childcount.models.logs import MessageLog

from libreport.pdfreport import PDFReport
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()
Elements = []

HeaderStyle = styles["Heading1"]


def header(txt, style=HeaderStyle, klass=Paragraph, sep=0.3):
    '''Creates a reportlab PDF element and adds it to the global Elements list

    style - can be a HeaderStyle, a ParaStyle or a custom style, default
            HeaderStyle
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


def index(request):
    '''Index page '''
    template_name = "childcount/index.html"
    todo = "To add child count here"
    return render_to_response(request, template_name, {
            "todo": todo})


def report_view(req):
    cls = ReportMalnutrition

    report_title = cls._meta.verbose_name
    rows = []

    reports = cls.objects.all()
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"].append({"value": report.case})
        row["cells"].append({"value": report.reporter})
        row["cells"].append({"value": \
                report.entered_at.strftime("%d/%m/%Y")})
        row["cells"].append({"value": report.muac, "num": True})
        row["cells"].append({"value": report.height, "num": True})
        row["cells"].append({"value": report.weight, "num": True})
        row["cells"].append({"value": report.status})

        if i == 100:
            row['complete'] = True
            rows.append(row)
            break
        rows.append(row)

    columns, sub_columns = cls.table_columns()

    aocolumns_js = "{ \"sType\": \"html\" },"
    for col in columns[1:] + (sub_columns if sub_columns != None else []):
        if not 'colspan' in col:
            aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                            "\"bSearchable\": false },"
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
    context_dict = {'get_vars': req.META['QUERY_STRING'],
                    'columns': columns, 'sub_columns': sub_columns,
                    'rows': rows, 'report_title': report_title,
                    'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

    if req.method == 'GET' and 'excel' in req.GET:
        '''response = HttpResponse(mimetype="application/vnd.ms-excel")
        filename = "%s %s.xls" % \
                   (report_title, datetime.now().strftime("%d%m%Y"))
        response['Content-Disposition'] = "attachment; " \
                                          "filename=\"%s\"" % filename
        from findug.utils import create_excel
        response.write(create_excel(context_dict))
        return response'''
        return render_to_response(req, 'childcount/report.html', context_dict)
    else:
        return render_to_response(req, 'childcount/report.html', context_dict)


def commands_pdf(request):
    '''List of supported commands and their format'''
    pdfrpt = PDFReport()
    pdfrpt.setLandscape(True)
    pdfrpt.setNumOfColumns(2)
    pdfrpt.setFilename("shortlist")
    header("Malnutrition Monitoring Report")

    p("MUAC +PatientID MUACMeasurement Edema (E/N) Symptoms")
    pre("Example: MUAC +1410 105 E V D Or      MUAC +1385 140 n")

    header("Malaria Rapid Diagnostic Test Reports (MRDT)")
    p("MRDT +PatientID RDTResult (Y/N) BedNet (Y/N) Symtoms")
    pre("Example: MRDT +28 Y N D CV")

    pre('''\

     Code | Symptom                 | Danger Sign
     =============================================
      CG  |  Coughing               |
      D   |  Diarrhea               |  CMAM
      A   |  Appetite Loss          |  CMAM
      F   |  Fever                  |  CMAM
      V   |  Vomiting               |  CMAM, RDT
      NR  |  Nonresponsive          |  CMAM, RDT
      UF  |  Unable to Feed         |  CMAM, RDT
      B   |  Breathing Difficulty   |  RDT
      CV  |  Convulsions/Fits       |  RDT
      CF  |  Confusion              |  RDT
     ==============================================
    ''')

    header("Death Report")
    p("DEATH LAST FIRST GENDER AGE  DateOfDeath (DDMMYY) CauseOfDeath "\
      "Location Description")
    pre("Example: DEATH RUTH BABE M 50m 041055 S H Sudden heart attack")

    header("Child Death Report")
    p("CDEATH +ID DateOfDeath(DDMMYY) Cause Location Description")
    pre("Example: CDEATH +782 101109 I C severe case of pneumonia")

    pre('''\
    CauseOfDeath - Likely causes of death
    ===========================
    P   |   Pregnancy related
    B   |   Child Birth
    A   |   Accident
    I   |   Illness
    S   |   Sudden Death
    ===========================
    ''')

    pre('''\
    Location - where the death occurred
    ===================================================
    H   |   Home
    C   |   Health Facility
    T   |   Transport - On route to Clinic/Hospital
    ===================================================
    ''')

    header("Birth Report")
    p("BIRTH Last First Gender(M/F) DOB (DDMMYY) WEIGHT Location "\
      "Guardian Complications")
    pre("BIRTH Onyango James M 051009 4.5 C Anyango No Complications")

    header("Inactive Cases")
    p("INACTIVE +PID ReasonOfInactivity")
    pre(" INACTIVE +23423 immigrated to another town(Siaya)")

    header("Activate Inactive Cases")
    p("ACTIVATE +PID ReasonForActivating")
    pre(" ACTIVATE +23423 came back from Nairobi")

    pdfrpt.setElements(Elements)
    return pdfrpt.render()


def patient_history(request):
    '''Patient History'''
    template_name = "childcount/history.html"

    all = []

    cases = Case.objects.filter(status=Case.STATUS_DEAD)
    for c in cases:

        row = {}
        row['report'] = {}
        row['case'] = c.get_dictionary()

        muac = ReportMalnutrition.objects.filter(case=c).order_by('entered_at')
        row['report']['muac'] = []
        for mr in muac:
            row['report']['muac'].append({'name': 'muac', \
                                          'result': '%smm' % mr.muac, \
                    'date': mr.entered_at.strftime("%d-%m-%Y"), 'object': mr, \
                                  'description': ''})

        mrdt = ReportMalaria.objects.filter(case=c).order_by('entered_at')
        row['report']['mrdt'] = []
        for mr in mrdt:
            row['report']['mrdt'].append({'name': 'mrdt', \
                            'result': mr.results_for_malaria_result(), \
                    'date': mr.entered_at.strftime("%d-%m-%Y"), 'object': mr, \
                                  'description': ''})

        measles = ReportMeasles.objects.filter(case=c).order_by('entered_at')
        row['report']['measles'] = []
        for ms in measles:
            result = 'no'
            if ms.taken == True:
                result = 'yes'
            row['report']['measles'].append({'name': 'measles', \
                                             'result': result, \
                    'date': ms.entered_at.strftime("%d-%m-%Y"), 'object': ms, \
                                  'description': ''})

        ml = MessageLog.objects.filter(text__icontains='+%s' % c.ref_id, \
                            was_handled=True).order_by('created_at')

        measles_bool = False
        death_bool = False
        log = []
        for i in ml:
            name = ''
            data = ''
            if re.match('muac', i.text, re.IGNORECASE):
                name = 'muac'
                data = row['report']['muac']
            elif re.match('mrdt', i.text, re.IGNORECASE):
                name = 'mrdt'
                data = row['report']['mrdt']
            elif re.match('inactive', i.text, re.IGNORECASE):
                name = 'inactive'
                l = len('%s +%s' % (name, c.ref_id)) + 1
                data = [{'name':'inacive', 'result': '', \
                        'date': i.created_at.strftime("%d-%m-%Y"), \
                        'object': i, 'description': i.text[l:]}]
            elif re.match('measles', i.text, re.IGNORECASE):
                name = 'measles'
                data = row['report']['measles']
                if not measles_bool:
                    measles_bool = True
                else:
                    continue
            elif re.match('cdeath', i.text, re.IGNORECASE):
                try:
                    death = ReportDeath.objects.filter(case=c).latest()
                    row['report']['death'] = [{'name':'death', \
                                               'result': 'dead', \
                            'date': death.entered_at.strftime("%d-%m-%Y"), \
                            'object': death, 'description': death.description}]
                except:
                    row['report']['death'] = [{'name':'death', \
                                               'result': 'dead', \
                            'date': i.created_at.strftime("%d-%m-%Y"), \
                            'object': i, 'description': i.text}]
                name = 'death'
                data = row['report']['death']
                if not death_bool:
                    death_bool = True
                else:
                    continue

            if len(data):
                data = data.pop()
            if name == '':
                data = {'name': 'unknown', 'result': '', \
                    'date': i.created_at.strftime("%d-%m-%Y"), 'object': i, \
                                              'description': i.text}
            log.append({'date': i.created_at.strftime('%d-%m-%Y'), \
                        'text': i.text, 'name': name, 'report': data})

        row["history"] = log
        all.append(row)
    return render_to_response(request, template_name, {
            "patients": all})
