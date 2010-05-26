#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context

from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import ThePatient

from libreport.pdfreport import PDFReport, p


def all_patient_list_pdf(request, rfilter=u'all', rformat="html"):
    report_title = ThePatient._meta.verbose_name
    rows = []
    if rfilter == 'underfive':
        reports = ThePatient.under_five()
    else:
        reports = ThePatient.objects.all().order_by('chw', 'household')

    columns, sub_columns = ThePatient.patients_summary_list()

    if rformat == 'pdf':
        for report in reports:
            rows.append([data for data in columns])
    
        rpt = PDFReport()
        rpt.setTitle(report_title)
        rpt.setFilename('_'.join(report_title.split()) + '.pdf')
        rpt.setTableData(reports, columns, _("All Patients"))
        return rpt.render()
    else:
        i = 0
        for report in reports:
            i += 1
            row = {}
            row["cells"] = [{'value': \
                             Template(col['bit']).render(Context({'object': \
                                                report}))} for col in columns]
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
        aocolumns_js = aocolumns_js[:-1]
    
        aggregate = False
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
            return render_to_response(request, 'childcount/patient.html', context_dict)
        else:
            return render_to_response(request, 'childcount/patient.html', context_dict)


def all_patient_list_per_chw_pdf(request):
    report_title = ThePatient._meta.verbose_name

    rpt = PDFReport()
    rpt.setTitle(report_title)
    rpt.setFilename('_'.join(report_title.split()) + '.pdf')
    rpt.setRowsPerPage(42)

    columns, sub_columns = ThePatient.patients_summary_list()

    chws = TheCHWReport.objects.all()
    for chw in chws:
        rows = []
        reports = ThePatient.objects.filter(chw=chw).order_by('household')
        summary = u"Number of Children: %(num)s" % {'num': reports.count()}
        for report in reports:
            rows.append([data for data in columns])

        sub_title = u"%s %s" % (chw, summary)
        #rpt.setElements([p(summary)])
        rpt.setTableData(reports, columns, chw, hasCounter=True)
        rpt.setPageBreak()

    return rpt.render()


def under_five(request):
    report_title = ThePatient._meta.verbose_name

    rpt = PDFReport()
    rpt.setTitle(report_title)
    rpt.setFilename('_'.join(report_title.split()) + '.pdf')
    rpt.setRowsPerPage(42)

    columns, sub_columns = ThePatient.patients_summary_list()

    chws = TheCHWReport.objects.all()
    for chw in chws:
        rows = []
        reports = ThePatient.under_five(chw)
        summary = u"Number of Children: %(num)s" % {'num': reports.count()}
        for report in reports:
            rows.append([data for data in columns])

        sub_title = u"%s %s" % (chw, summary)
        #rpt.setElements([p(summary)])
        rpt.setTableData(reports, columns, chw, hasCounter=True)
        rpt.setPageBreak()

    return rpt.render()


def chw(request, rformat='html'):
    '''Community Health Worker page '''
    report_title = TheCHWReport._meta.verbose_name
    rows = []

    reports = TheCHWReport.objects.filter(role__code='chw')
    columns, sub_columns = TheCHWReport.summary()
    if rformat.lower() == 'pdf':
        rpt = PDFReport()
        rpt.setTitle(report_title)
        rpt.setFilename('_'.join(report_title.split()) + '.pdf')

        for report in reports:
            rows.append([data for data in columns])

        rpt.setTableData(reports, columns, report_title)
        rpt.setPageBreak()

        return rpt.render()
    else:
        i = 0
        for report in reports:
            i += 1
            row = {}
            row["cells"] = [{'value': \
                             Template(col['bit']).render(Context({'object': \
                                                report}))} for col in columns]
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
        aocolumns_js = aocolumns_js[:-1]
    
        aggregate = False
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
