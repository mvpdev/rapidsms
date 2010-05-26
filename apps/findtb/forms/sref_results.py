#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from datetime import date, timedelta

from django import forms
from django_tracking.models import State, TrackedItem

# this line needs to be that twisted to by pass recursive import
# TODO: use the django tool that let you import model indirectly
# to fix this
from findtb.forms.forms import SpecimenForm, PatientForm
from findtb.models.models import Patient
from findtb.models.sref_result_states import MicroscopyResult
from findtb.libs.utils import send_to_dtu
from sref_transit import SrefForm

"""
Forms setting states for a testing results
"""


class MicroscopyForm(SrefForm):
    """
    Form shown when the specimen needs a microcopy.
    """

    RESULT_CHOICES = (
        ('positive', u"Positive"),
        ('negative', u"Negative"),
        ('na', u"N/A"),
    )

    result = forms.ChoiceField(choices=ACTION_CHOICES)


    def save(self, *args, **kwargs):


        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)


        result = MicroscopyResult(result=self.clean_date['result']))
        ti.state = State(content_object=result, specimen=self.specimen))
        ti.save()

        msg = u"Microscopy results for specimen of %(patient)s with "\
              u"tracking tag %(tag)s: %s(result)s" {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.clean_date['result']}


        send_to_dtu(self.specimen.location, msg)

