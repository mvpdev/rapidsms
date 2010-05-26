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
from findtb.models.sref_generic_states import SpecimenInvalid,\
                                              SpecimenReceived,\
                                              SpecimenMustBeReplaced
from findtb.libs.utils import send_to_dtu

"""
Forms setting states for a specimen in transit from the dtu to the ntlr
"""


class SrefForm(forms.Form):
    """
    Common form used for all SREF forms. Gets passed a specimen object.
    """
    def __init__(self, specimen, *args, **kwargs):
        super(SrefForm, self).__init__(*args, **kwargs)
        self.specimen = specimen



class SrefRegisteredReceived(SrefForm):
    """
    Form shown when the specimen is in the registered state.
    """

    ACTION_CHOICES = (
        ('received', u"Received"),
        ('invalid_request', u"Invalid: Request new specimen"),
        ('invalid', u"Invalid"),
    )

    age = forms.IntegerField(min_value=0,
                             max_value=150,
                             widget=forms.TextInput(attrs={'size':'10'}),
                             required=False)

    chosen_action = forms.ChoiceField(choices=ACTION_CHOICES)

    class Media:
        js = ('/static/findtb/js/sref_registered.js',)


    def __init__(self, specimen, *args, **kwargs):

        super(SrefRegisteredReceived, self).__init__(specimen, *args, **kwargs)

        self.patient_form = PatientForm(instance=self.specimen.patient,
                                        *args, **kwargs)

        self.specimen_form = SpecimenForm(instance=self.specimen,
                                          *args, **kwargs)

        # these form have no requirement, force it for this instance
        self.patient_form.fields['gender'].required = True
        self.specimen_form.fields['tc_number'].required = True


    def is_valid(self):
        """
        Validation is made on the current form and, if the action is
        receiving the specimen, on the patient and specimen form.
        """

        valid = super(SrefRegisteredReceived, self).is_valid()

        if self.data['chosen_action'] == 'received':
            valid = valid and self.patient_form.is_valid() \
                          and self.specimen_form.is_valid()

            self.errors.update(self.specimen_form.errors)
            self.errors.update(self.patient_form.errors)

        return valid



    def save(self, *args, **kwargs):
        """
        Get the patient's int age and calculate an approximate date of birht.
        Save the next state of the SPUTUM, depending on the chosen_action
        """


        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        action = self.cleaned_data['chosen_action']
        requested = 'request' in action
        action = action.split('_')[0]

        if action == 'received':

            # change the age in an estimated date of birth
            if self.cleaned_data['age'] is not None:
                WEEKS_IN_YEAR = 52.17745
                weeks = WEEKS_IN_YEAR * (self.cleaned_data['age'] + 0.5)
                self.specimen.patient.dob = date.today() - timedelta(weeks=weeks)

            self.specimen_form.save()
            self.patient_form.save()

            state = SpecimenReceived(specimen=self.specimen)
            ti.state = state

            msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                  u"received at NTLS. TC number is now %(tc_number)s." %\
                  {'patient': self.specimen.patient,
                   'tag': self.specimen.tracking_tag,
                   'tc_number': self.specimen.tc_number}

        else:

            if action == 'lost':
                if requested:

                    result  = SpecimenInvalid(cause=action,
                                             specimen=self.specimen)
                    ti.state = State(content_object=result)
                    ti.save()
                    result = SpecimenMustBeReplaced(specimen=self.specimen)
                    ti.state = State(content_object=result, is_final=True)

                    msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                          u"has been lost. Please send a new specimen." %\
                          {'patient': self.specimen.patient,
                           'tag': self.specimen.tracking_tag}

                else:

                    result = SpecimenInvalid(cause=action,
                                             specimen=self.specimen)
                    ti.state = State(content_object=result, is_final=True)

                    msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                          u"has been lost. There is nothing to do." %\
                          {'patient': self.specimen.patient,
                           'tag': self.specimen.tracking_tag}

            else:
                if requested:

                    result = SpecimenInvalid(cause=action,
                                             specimen=self.specimen)
                    ti.state = State(content_object=result)
                    ti.save()
                    result = SpecimenMustBeReplaced(specimen=self.specimen)
                    ti.state = State(content_object=result, is_final=True)

                    msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                          u"has been declared invalid by NTLS. "\
                          u"Please send a new specimen." %\
                          {'patient': self.specimen.patient,
                           'tag': self.specimen.tracking_tag}

                else:

                    result = SpecimenInvalid(cause=action,
                                             specimen=self.specimen)
                    ti.state = State(content_object=result, is_final=True)

                    msg = u"Specimen of %(patient)s with tracking tag %(tag)s "\
                          u"has been declared invalid by NTLS. "\
                          u"There is nothing to do." %\
                          {'patient': self.specimen.patient,
                           'tag': self.specimen.tracking_tag}


        send_to_dtu(self.specimen.location, msg)
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
            return SpecimenReceived(specimen=self.specimen)

        if requested:
            if action == 'invalid':
                pass # Send SMS
            elif action == 'lost':
                pass # Send SMS

        # only invalid or lost
        return State(content_object=SpecimenInvalid(cause=action,
                                                    specimen=self.specimen),
                     is_final=True)
