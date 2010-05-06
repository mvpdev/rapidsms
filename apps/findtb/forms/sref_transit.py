#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from datetime import date, timedelta

from django import forms

from django_tracking.models import State, TrackedItem

# this line needs to be that twisted to by pass recursive import
from findtb.forms.forms import SpecimenForm, PatientForm
from findtb.models.models import Patient
from findtb.models.sref import  SpecimenInvalid, SpecimenReceived

"""
Forms setting states for a specimen in transit from the dtu to the ntlr
"""


class SrefForm(forms.Form):
    """
    Common form used for all SREF forms. Gets passed a specimen object.
    """
    def __init__(self, data, specimen, *args, **kwargs):
        super(SrefForm, self).__init__(*args, **kwargs)
        self.specimen = specimen




# TODO : grey the part of the form that are not usefull if we decide it's lost
class SrefRegisteredReceived(SrefForm):
    """
    Form shown when the specimen is in the registered state.
    """

    ACTION_CHOICES = (
        ('received', u"Received"),
        ('invalid_request', u"Invalid: Request new specimen"),
        ('invalid', u"Invalid")
    )

    age = forms.IntegerField(min_value=0, max_value=150,
                            widget=forms.TextInput(attrs={'size':'14'}))
    chosen_action = forms.ChoiceField(choices=ACTION_CHOICES)


    def __init__(self, data, *args, **kwargs):
        super(SrefRegisteredReceived, self).__init__(data, *args, **kwargs)
        self.patient_form = PatientForm(data,
                                        instance=self.specimen.patient)
        self.specimen_form = SpecimenForm(data,
                                        instance=self.specimen)


    def is_valid(self):
        return super(SrefRegisteredReceived, self).is_valid()\
               and self.patient_form.is_valid()\
               and self.specimen_form.is_valid()


    def clean_age(self):
        """
        Calculate the estimated date of birth.
        """
        WEEKS_IN_YEAR = 52.17745
        weeks = WEEKS_IN_YEAR * (self.cleaned_data['age'] + 0.5)
        self.cleaned_data['dob'] = date.today() - timedelta(weeks=weeks)


    def save(self, *args, **kwargs):
        """
        Get the patient's int age and calculate an approximate dob. Save
        the next state of the SPUTUM, depending on the chosen_action
        """

        self.specimen_form.save()
        self.patient_form.save()

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        action = self.cleaned_data['chosen_action']
        requested = 'request' in action
        action = action.split('_')[0]

        if action == 'received':
            ti.state = SpecimenReceived(specimen=self.specimen)

        else:
            # only invalid or lost
            ti.state = State(content_object=SpecimenInvalid(action, self.specimen),
                                is_final=True)
            if requested:
                pass # Send SMS
            else:
                pass
        ti.save()


class SrefLostOrReceived(SrefRegisteredReceived):
    """
    Form shown in webui when specimen is in the sent state.
    """
    class Meta:
        model = Patient
        exclude = ('created_by', 'created_on', 'location', \
                   'registration_number', 'estimated_dob', 'dob')

    ACTION_CHOICES = SrefRegisteredReceived.ACTION_CHOICES + (
        ('lost_request', u"Lost: Request new specimen"),
        ('lost', u"Lost"),
    )

    def get_next_state(self):
        # TODO Send SMSs for all different states below
        action = self.cleaned_data['chosen_action']
        requested = 'request' in action
        action = action.split('_')[0]

        if action == 'received':
            return SpecimenReceived(self.specimen)

        if requested:
            if action == 'invalid':
                pass # Send SMS
            elif action == 'lost':
                pass # Send SMS

        # only invalid or lost
        return State(content_object=SpecimenInvalid(action, self.specimen),
                     is_final=True)
