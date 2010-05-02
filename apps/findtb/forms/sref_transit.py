#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from datetime import date, timedelta

from django import forms

from findtb.models import Patient

Class SrefForm(forms.Form):
    """
    Common form used for all SREF forms. Gets passed a specimen object.
    """
    def __init__(self, specimen, *args, **kwargs):
        self.specimen = specimen
        super(SrefForm, self).__init__(*args, **kwargs)
    

Class SrefReceived(SrefForm):
    """
    Form shown when the specimen is in the registered state.
    """
    ACTION_CHOICES = (
        ('received', u"Received"),
        ('invalid_request', u"Invalid: Request new specimen")
        ('invalid', u"Invalid")

    )

    age = forms.IntegerField()
    chosen_action = forms.CharField(choices=ACTION_CHOICES)
    tc_number = forms.CharField(max_length=12)

    def clean_tc_number(self):
        """
        Ensures that the tc_number entered in the form is not already in the
        db. Raise exception if it is.
        """
        
        try:
            existing = Specimen.objects \ 
                             .get(tc_number=self.cleaned_data['tc_number']):
        except Specimen.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(u"TC number %(num)s has already been "\
                                        u"issued to a specimen for " \
                                        u"patient %(patient)s" % \
                                        {'num':existing.tc_number, \
                                         'patient':existing.patient})

    # TODO Clean age. Restrict to logical values

    def save(self):
        """
        Get the patient's int age and calculate an approximate dob. Save
        the next state of the SPUTUM, depending on the chosen_action
        """
        WEEKS_IN_YEAR = 52.17745
        age = self.cleaned_data['age']
        dob = date.today() - timedelta(weeks = WEEKS_IN_YEAR * (age + 0.5))
        patient = self.specimen.patient
        patient.dob = dob
        self.specimen.tc_number = self.cleaned_data['tc_number']
        specimen.save()
        
        s = self.get_next_state()
        s.save()
        TrackedItem.add_state_to_item(specimen, self.get_next_state())

        patient.save()


    def get_next_state(self):
        # TODO Send SMSs for all different states below
        action = cleaned_data['chosen_action']
        requested = 'request' in action
        action = action.split('_')[0]
        
        if action == 'received':
            return SpecimenReceieved(self.specimen)

        if requested:
            pass # Send SMS

        # only invalid or lost
        return State(content_object=SpecimenInvalid(action, self.specimen),
                     final=True)



Class SrefLostOrReceived(SrefReceived):
    """
    Form shown in webui when specimen is in the sent state.
    """
    class Meta:
        model = Patient
        exclude = ('created_by', 'created_on', 'location', \
                   'patient_id', 'estimated_dob', 'dob')

    ACTION_CHOICES = SrefReceived.ACTION_CHOICES + (
        ('lost_request', u"Lost: Request new specimen"),
        ('lost', u"Lost"),
    )

    def get_next_state(self):
        # TODO Send SMSs for all different states below
        action = cleaned_data['chosen_action']
        requested = 'request' in action
        action = action.split('_')[0]
        
        if action == 'received':
            return SpecimenReceieved(self.specimen)

        if requested:
            if action == 'invalid':
                pass # Send SMS
            elif action == 'lost':
                pass # Send SMS

        # only invalid or lost
        return State(content_object=SpecimenInvalid(action, self.specimen),
                     final=True)
