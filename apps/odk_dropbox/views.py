#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import re
from datetime import datetime

from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render_to_response
from django.http import HttpResponse

from models import Form, Submission, SubmissionImage, ODK_DATE_FORMAT

def form_list(request):
    forms = Form.objects.all()
    return render_to_response("form_list.html", {'forms':forms})

def submission_list(request):
    forms = Form.objects.all()
    return render_to_response("submission_list.html", {'forms':forms})

@require_GET
def odk_list_forms(request):
    d = {}
    for f in Form.objects.filter(active=True):
        e = {"host" : request.get_host(),
             "form_url" : f.url()}
        d[f.name] = "http://%(host)s/%(form_url)s" % e
    return render_to_response("odk_list_forms.xml",
                              {'files': d},
                              mimetype="application/xml")

@require_GET
def odk_get_form(request, name):
    f = Form.objects.get(name=name, active=True)
    return HttpResponse(f.xml, mimetype="application/xml")

ODK_DATE_REGEXP = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"
NAME_REGEXP = r"(?P<name>.*)"
FORM_REGEXP = NAME_REGEXP + r"\.xml$"
SUBMISSION_REGEXP = NAME_REGEXP + r"_(?P<time_stamp>" + ODK_DATE_REGEXP + r")\.xml$"

@require_POST
def odk_submission(request):
    # request.FILES is a django.utils.datastructures.MultiValueDict
    # for each key we have a list of values
    xml_file_list = request.FILES.pop("xml_submission_file")
    assert len(xml_file_list)==1, "There should be a single xml file in this submission."
    xml_file = xml_file_list[0]

    # get the form that shares the name of this submission
    m = re.match(SUBMISSION_REGEXP, xml_file.name)
    assert m, "This file name didn't match the ODK Collect naming pattern."
    saved = datetime.strptime(m.group("time_stamp"), ODK_DATE_FORMAT)

    xml_file.open()
    xml = xml_file.read()
    xml_file.close()
    s = Submission(xml=xml, saved=saved)
    s.save()

    # save the rest of the files to the filesystem
    # these should all be images
    for key in request.FILES.keys():
        for image in request.FILES.getlist(key):
            SubmissionImage.objects.create(submission=s, image=image)

    # I should do some parsing in here
    # CAN I SEND A USEFUL ERROR MESSAGE LIKE YOU NEED TO UPDATE YOUR FORM
    # DO I WANT TO SEND SUCH A MESSAGE?
    # if not s.form.active:
    #     # we need to let the surveyor know this form is no longer active
    #     pass

    # ODK needs two things for a form to be considered successful
    # 1) the status code needs to be 201 (created)
    # 2) The location header needs to be set to the host it posted to
    response = HttpResponse("You've successfully made an odk submission.")
    response.status_code = 201
    response['Location'] = "http://%s/submission" % request.get_host()
    return response


# I need a view where a user can upload a form using an xml file
