#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from django.forms import ModelForm
from findtb.models.models import Patient, Specimen

# Create the form class.
class PatientForm(ModelForm):
     class Meta:
         model = Patient
         fields = ('gender', 'last_name', 'first_name', )


# Create the form class.
class SpecimenForm(ModelForm):
     class Meta:
         model = Specimen
         fields = ('tc_number',)


