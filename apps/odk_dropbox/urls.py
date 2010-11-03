#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from . import views
from .models import ODK_FORMS

urlpatterns = patterns('',
    # list that ODK Collect uses to download forms
    url(r"^formList$", views.odk_list_forms),

    # url where ODK Collect submits data
    url(r"^submission$", views.odk_submission),

    # urls that serve the forms
    url(r"^" + ODK_FORMS + views.FORM_REGEXP, views.odk_get_form),
    
    # Web UI:
    # UI: View Submissions
    url(r"^submissions$", views.submission_list),
    # UI: View Forms
    url(r"^forms$", views.form_list),
)
