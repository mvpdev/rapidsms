#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from django.forms import ModelForm
from findtb.models.models import Patient, Specimen, Slide, SlidesBatch

class PatientForm(ModelForm):
     class Meta:
         model = Patient
         fields = ('gender', 'last_name', 'first_name', )


class SpecimenForm(ModelForm):
     class Meta:
         model = Specimen
         fields = ('tc_number',)


class SlidesBatchForm(ModelForm):
     class Meta:
         model = SlidesBatch
         fields = ('comment',)




