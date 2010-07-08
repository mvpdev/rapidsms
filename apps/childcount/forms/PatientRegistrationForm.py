#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from datetime import date, datetime

from django.db import models
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.utils import clean_names, DOBProcessor
from childcount.models import Patient, Encounter, HealthId, CHWHealthId
from locations.models import Location
from childcount.exceptions import BadValue, ParseError
from childcount.forms.utils import MultipleChoiceField


class PatientRegistrationForm(CCForm):
    KEYWORDS = {
        'en': ['new'],
        'fr': ['new'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT
    MIN_HH_AGE = 10
    MULTIPLE_PATIENTS = False

    gender_field = MultipleChoiceField()
    gender_field.add_choice('en', Patient.GENDER_MALE, 'M')
    gender_field.add_choice('en', Patient.GENDER_FEMALE, 'F')
    gender_field.add_choice('fr', Patient.GENDER_MALE, 'M')
    gender_field.add_choice('fr', Patient.GENDER_FEMALE, 'F')

    PREVIOUS_ID = {'en': 'H', 'fr': 'H'}

    SURNAME_FIRST = False

    def pre_process(self):
        health_id = self.health_id

        print self.date

        try:
            p = Patient.objects.get(health_id__iexact=health_id)
        except Patient.DoesNotExist:
            pass
        else:
            raise BadValue(_(u"That health ID has already been issued to "\
                              "%(patient)s by %(chw)s") % \
                             {'patient': p, 'chw': p.chw})

        valid_statuses = [HealthId.STATUS_GENERATED, HealthId.STATUS_PRINTED]
        try:
            health_id_obj = HealthId.objects.get(health_id__iexact=health_id, \
                                                 status__in=valid_statuses)
        except HealthId.DoesNotExist:
            raise BadValue(_(u"That health ID (%(id)s) is not valid." % \
                              {'id': health_id.upper()}))

        patient = Patient()
        patient.health_id = health_id
        patient.chw = self.chw
        tokens = self.params[1:]

        lang = self.message.reporter.language

        expected = _(u"| location | patient names | gender | age or " \
                      "DOB | head_of_household |")

        if len(tokens) < 5:
            raise ParseError(_(u"Not enough info. Expected: " \
                                "%(expected)s") % {'expected': expected})

        location_code = tokens.pop(0)
        try:
            location = Location.objects.get(code__iexact=location_code)
        except Location.DoesNotExist:
            raise BadValue(_(u"%(loc)s is not a valid location code. You " \
                              "must indicate the patient's location code " \
                              "before his name.") % \
                              {'loc': location_code})

        patient.location = location

        self.gender_field.set_language(lang)

        gender_indexes = []
        i = 0
        for token in tokens:
            if token in self.gender_field.valid_choices():
                gender_indexes.append(i)
            i += 1

        if len(gender_indexes) == 0:
            raise ParseError(_(u"You must indicate gender after the name " \
                                "with a %(choices)s.") % \
                              {'choices': self.gender_field.choices_string()})

        dob = None
        for i in gender_indexes:
            # the gender field is at the end of the tokens.  We don't know
            # what to do about this.
            if i == len(tokens) - 1:
                raise ParseError(_(u"Message not understood. Expected: " \
                                    "%(expected)s") % \
                                    {'expected': expected})

            dob, variance = DOBProcessor.from_age_or_dob(lang, tokens[i + 1], \
                                                         self.date.date())

            if dob:
                patient.dob = dob
                days, weeks, months = patient.age_in_days_weeks_months()
                if days < 60 and variance > 1:
                    raise BadValue(_(u"You must provide an exact birth date " \
                                      "for children under 2 months."))
                elif months < 24 and variance > 30:
                    raise BadValue(_(u"You must provide an exact birth date " \
                                      "or the age, in months, for children " \
                                      "under two years."))

        if not dob:
            raise ParseError(_(u"Could not understand age or " \
                                    "date_of_birth of %(string)s.") % \
                                    {'string': tokens[i + 1]})

        patient.estimated_dob = variance > 1

        # if the gender field is the first or second
        if i == 0:
            raise ParseError(_(u"You must provide a patient name before " \
                                "their sex."))

        patient.last_name, patient.first_name, alias = \
                             clean_names(' '.join(tokens[:i]), \
                             surname_first=self.SURNAME_FIRST)

        # remove the name tokens
        tokens = tokens[i:]

        # remove the gender token
        patient.gender = self.gender_field.get_db_value(tokens.pop(0))

        # remove the age token
        tokens.pop(0)

        if len(tokens) == 0:
            raise ParseError(_(u"You must indicate the head of " \
                                "household after the age. If this " \
                                "is the head of household, " \
                                "write %(char)s after the dob/age.") % \
                                {'char': self.PREVIOUS_ID[lang]})

        household = tokens.pop(0)
        self_hoh = False
        if household == self.PREVIOUS_ID[lang].lower():
            if patient.years() < self.MIN_HH_AGE:
                raise BadValue(_(u"This patient is too young to be a head of "\
                                  "household. You must provide the correct "\
                                  "head of household."))
            patient.household = patient
            self_hoh = True

        # Patient is not a head of household
        else:
            try:
                patient.household = Patient.objects.get( \
                                                health_id__iexact=household)
            except Patient.DoesNotExist:
                raise BadValue(_(u"Could not find head of household " \
                                  "with health ID %(id)s. You must " \
                                  "first register the head of household.") % \
                                  {'id': household})

            age = patient.household.years()
            if age < self.MIN_HH_AGE:
                raise BadValue(_(u"The head of household you specified is " \
                                  "too young to be a head of household " \
                                  "(%(hh)s).") % {'hh': patient.household})

            # if the household head they listed is not a head of household
            if patient.household.household != patient.household:
                raise BadValue(_(u"The head of household you specified " \
                                  "(%(hh)s) is not a head of household. " \
                                  "His head of household is (%(hhhh)s). " \
                                  "If he is the head, set him head of " \
                                  "household.") % \
                                  {'hh': patient.household, \
                                   'hhhh': patient.household.household, \
                                   'char': self.PREVIOUS_ID[lang]})

        patient_check = Patient.objects.filter( \
                                first_name__iexact=patient.first_name, \
                                last_name__iexact=patient.last_name, \
                                dob=patient.dob)

        if len(patient_check) > 0:
            old_p = patient_check[0]
            if old_p.chw == self.chw:
                patient_chw = _(u"you")
            else:
                patient_chw = patient_check[0].chw
            raise BadValue(_(u"%(name)s %(sex)s/%(age)s was already " \
                              "registered by %(chw)s. Their health id is " \
                              "%(id)s.") % \
                              {'name': old_p.full_name(), \
                               'sex': old_p.gender, \
                               'age': old_p.humanised_age(), \
                               'chw': patient_chw, \
                               'id': old_p.health_id.upper()})
        patient.save()
        if self_hoh:
            patient.household = patient
            patient.save()

        health_id_obj.issued_to = patient
        health_id_obj.issued_on = datetime.now()
        health_id_obj.status = HealthId.STATUS_ISSUED
        health_id_obj.save()

        #indicate the health id as being used by a chw
        try:
            if CHWHealthId.objects.filter(health_id=health_id_obj):
                chw_healthid_obj =\
                    CHWHealthId.objects.get(health_id=health_id_obj)
                chw_healthid_obj.used = True
                chw_healthid_obj.chw = patient.chw
                chw_healthid_obj.save()
        except:
            pass

        self.response = _("You successfuly registered %(patient)s.") % \
                    {'patient': patient}
