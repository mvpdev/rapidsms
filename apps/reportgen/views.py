#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import sys
import traceback
import socket
import simplejson

from datetime import datetime

from celery.task.control import inspect

from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.http import HttpResponse
from django.template import Context
from django.template import loader

from rapidsms.webui.utils import render_to_response

from reportgen.models import Report
from reportgen.models import GeneratedReport

from reportgen.utils import DISPLAY_REPORTS_MAX
from reportgen.utils import ondemand_json_obj

from reportgen.timeperiods import period_type_for

@login_required
def ondemand(request):
    data = {}
    if request.method == "POST":
        return _process_gen(request)
    data['title'] = _('On-Demand Reports')
    data['gen'] = GeneratedReport.objects.order_by('-started_at')[0:DISPLAY_REPORTS_MAX]
    data['data'] = ondemand_json_obj()
    
    data['choices'] = simplejson.dumps(GeneratedReport.TASK_STATE_DICT)

    # Get status of celery workers
    # Data workers is a tuple of (is_rabbitmq_up, n_workers)
    i = inspect()
    try:
        p = i.ping()
    except Exception as e:
        data['workers'] = (False, e)
    else:
        if p and len(p) > 0:
            data['workers'] = (True, len(p))
        else:
            data['workers'] = (True, 0)

    return render_to_response(request, "ondemand.html", data)

def _process_gen(request):
    args = {}
    report = Report.objects.get(pk=request.POST['report_pk'])
    d = report.get_definition()

    for v in d.variants:
        if request.POST['variant_index'] == v[1]:
            print "%s %s" % (request.POST['variant_index'], v)
            args['variant'] = v
            break

    if 'variant' not in args and request.POST['variant_index'] != 'X':
        print "&&&%s" % args
        raise ValueError(_("Variant not found"))
        
    args['rformat'] = request.POST['rformat']

    period_type = period_type_for(request.POST['period_type_code'])
    pindex = int(request.POST['period_index'])
    args['time_period'] = period_type.periods()[pindex]

    if args['rformat'] not in d.formats:
        raise ValueError('Invalid report format')

    gr = GeneratedReport()
    gr.filename = ''
    gr.title = d.title
    if 'variant' in args:
        gr.variant_title = args['variant'][0]
    gr.report = report
    gr.fileformat = args['rformat']
    gr.period_title = args['time_period'].title
    gr.task_progress = 0
    gr.task_state = GeneratedReport.TASK_STATE_PENDING
    gr.started_at = datetime.now()
    gr.save()

    args['generated_report'] = gr

    print args
    try:
        r = d.apply_async(kwargs=args)
    except socket.error:
        gr.task_state = GeneratedReport.TASK_STATE_FAILED
        gr.finished_at = datetime.now()
        gr.task_progress = 0
        gr.error_message = ''.join(traceback.format_exception(*sys.exc_info()))
        gr.save()
    else:
        gr.task_id = r.task_id
        gr.save()
    
    return HttpResponseRedirect('/reportgen/')

@login_required
def delete(request, pk):
    r = GeneratedReport.objects.get(pk=pk)
    r.delete()
    return HttpResponseRedirect('/reportgen/')

@login_required
def ajax_progress(request):
    reps = GeneratedReport\
        .objects\
        .order_by('-started_at')[0:DISPLAY_REPORTS_MAX]
 
    rows = {}
    errors = {}
    progresses = {}
    row_template = loader.get_template("status_row.html")
    error_template = loader.get_template("error_row.html")
    for r in reps:
        c = Context({'rep': r})
        rows[r.pk] = row_template.render(c)
        if r.is_failed:
            errors[r.pk] = error_template.render(c)
        if r.task_progress:
            progresses[r.pk] = r.task_progress

    return HttpResponse(simplejson.dumps([rows,errors,progresses]), \
                                mimetype="application/json")

