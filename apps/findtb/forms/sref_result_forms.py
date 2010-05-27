#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django import forms
from django_tracking.models import State, TrackedItem
from findtb.models import SpecimenMustBeReplaced

# this line needs to be that twisted to by pass recursive import
# TODO: use the django tool that let you import model indirectly
# to fix this
from findtb.models.sref_result_states import MicroscopyResult,\
                                             LpaResult,\
                                             MgitResult
from findtb.libs.utils import send_to_dtu
from sref_transit_forms import SrefForm

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

    result = forms.ChoiceField(choices=RESULT_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)



        result = MicroscopyResult(result=self.cleaned_data['result'],
                                  specimen=self.specimen)

        ti.state = result
        ti.save()

        msg = u"Microscopy results for specimen of %(patient)s with "\
              u"tracking tag %(tag)s: %(result)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.cleaned_data['result']}


        send_to_dtu(self.specimen.location, msg)



class LpaForm(SrefForm):
    """
    Form shown when the specimen needs a a LPA.
    """

    RIF_CHOICES = (
        ('resistant', u"RIF Resistant") ,
        ('susceptible', u"RIF suceptible"),
        ('na', u"N/A"),
    )

    INH_CHOICES = (
        ('resistant', u"INH Resistant") ,
        ('susceptible', u"INH suceptible"),
        ('na', u"N/A"),
    )

    rif = forms.ChoiceField(choices=RIF_CHOICES)
    inh = forms.ChoiceField(choices=INH_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)


        result = LpaResult(rif=self.clean_date['rif'],
                           inh=self.clean_date['inh'],
                           specimen=self.specimen)
        ti.state = result
        ti.save()

        msg = u"LPA results for specimen of %(patient)s with "\
              u"tracking tag %(tag)s: %s(inh)s and %s(rif)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'inh': self.clean_date['inh'],
               'rif': self.clean_date['rif']}


        send_to_dtu(self.specimen.location, msg)



class MgitForm(SrefForm):
    """
    Form shown when the specimen needs a MGIT.
    """

    RESULT_CHOICES = (
        ('positive', u"Positive"),
        ('negative', u"Negative"),
    )

    result = forms.ChoiceField(choices=RESULT_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        result = MgitResult(result=self.clean_date['result'],
                            specimen=self.specimen)
        ti.state = result
        ti.save()

        if self.clean_date['result'] == 'negative':
            result = SpecimenMustBeReplaced(specimen=self.specimen)
            ti.state = State(content_object=result, is_final=True)
            ti.save()

        msg = u"MGIT results for specimen of %(patient)s with "\
              u"tracking tag %(tag)s: %s(result)s" % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.clean_date['result']}


        send_to_dtu(self.specimen.location, msg)
