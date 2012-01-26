#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import os

from rapidsms.webui.utils import render_to_response
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseNotFound
from django.template import Template, Context, loader
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from django.db import IntegrityError
from childcount.models import HealthId


class UploadHealthIDFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()


@login_required
@permission_required('childcount.add_healthid')
def upload_file(request):
    ctx = {}
    if request.method == 'POST':
        form = UploadHealthIDFileForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            fn = title.strip().replace(' ', '_') + '.txt'
            fn = handle_uploaded_file(request.FILES['file'], fn)
            message = u"Succesfully uploaded health id file."
            c = load_healthids(fn)
            message += " %(count)s health ids added." % {'count': c}
            ctx = {'message': message}
        else:
            ctx = {'message': u"Invalid form Input", 'form': form}
    else:
        form = UploadHealthIDFileForm()
        ctx = {'form': form}
    return render_to_response(request, 'childcount/uploadhealthids.html', ctx)


def handle_uploaded_file(f, filename):
    fn = os.path.join(os.path.dirname(__file__), 'static', filename)
    destination = open(fn, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    return fn

def load_healthids(filename):
    c = 0
    if filename:
        with open(filename) as f:
            for line in f:
                line = line.strip()
                try:
                    HealthId.objects.create(
                        health_id = line,
                        status = HealthId.STATUS_GENERATED)
                    print "Adding health ID %s" % (line)
                    c += 1
                except IntegrityError:
                    print "Skipping health ID %s" % (line)
    return c
