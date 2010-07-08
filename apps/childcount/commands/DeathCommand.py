#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import datetime
import random

from django.utils.translation import ugettext as _

from reporters.models import Reporter
from locations.models import Location

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.utils import clean_names, DOBProcessor
from childcount.exceptions import BadValue, ParseError
from childcount.forms.utils import MultipleChoiceField
from childcount.models import DeadPerson, Patient


class DeathCommand(CCCommand):

    KEYWORDS = {
        'en': ['ddb'],
        'fr': ['ddb'],
    }

    MIN_HH_AGE = 10

    gender_field = MultipleChoiceField()
    gender_field.add_choice('en', DeadPerson.GENDER_MALE, 'M')
    gender_field.add_choice('en', DeadPerson.GENDER_FEMALE, 'F')

    SURNAME_FIRST = False

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw
        lang = self.message.reporter.language
        death = DeadPerson()
        death.chw = chw

        expected = _(u"dead person names | gender | age or " \
                      "DOB | date_of_death | [head_of_household]")
        if len(self.params) < 6:
            raise ParseError(_(u"Not enough information. Expected: " \
                                "%(keyword)s %(expected)s") % \
                                {'keyword': self.params[0], \
                                'expected': expected})

        tokens = self.params[1:]
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

        if not dob:
            raise ParseError(_(u"Could not understand age or " \
                                    "date_of_birth of %(string)s.") % \
                                    {'string': tokens[i + 1]})
        death.dob = dob
        # if the gender field is the first or second
        if i == 0:
            raise ParseError(_(u"You must provide a patient name before " \
                                "their sex."))

        death.last_name, death.first_name, alias = \
                             clean_names(' '.join(tokens[:i]), \
                             surname_first=self.SURNAME_FIRST)
 
        # remove the name tokens
        tokens = tokens[i:]

        # remove the gender token
        death.gender = self.gender_field.get_db_value(tokens.pop(0))

        # remove the age token
        tokens = tokens[1:]

        if len(tokens) == 0:
            raise ParseError(_(u"You must provide the date of death"))
        if len(tokens[0]) < 4:
            raise ParseError(_(u"Could not understand date_of_death of "\
                                "%(string)s. Please provide an exact date of"\
                                " death in the format DDMMYY.") % \
                                    {'string': tokens[0]})
        try:
            dod, variance = DOBProcessor.from_dob(lang, tokens[0], \
                                                  self.date.date())
        except:
            raise ParseError(_(u"Could not understand date_of_death of "\
                                "%(string)s. Please provide an exact date of"\
                                " death in the format DDMMYY.") % \
                                    {'string': tokens[0]})

        if not dod:
            raise ParseError(_(u"Could not understand " \
                                    "date_of_death of %(string)s.") % \
                                    {'string': tokens[0]})
        death.dod = dod

        #remove the dod token
        tokens.pop(0)

        if len(tokens) > 0:
            household = tokens.pop(0)
            
            # Patient is not a head of household
            try:
                death.household = Patient.objects.get( \
                                                health_id__iexact=household)
            except Patient.DoesNotExist:
                raise BadValue(_(u"Could not find head of household " \
                                  "with health ID %(id)s. You must " \
                                  "first register the head of household.") % \
                                  {'id': household})

            age = death.household.years()
            if age < self.MIN_HH_AGE:
                raise BadValue(_(u"The head of household you specified is " \
                                  "too young to be a head of household " \
                                  "(%(hh)s).") % {'hh': death.household})

            # if the household head they listed is not a head of household
            if death.household.household != death.household:
                raise BadValue(_(u"The head of household you specified " \
                                  "(%(hh)s) is not a head of household. " \
                                  "Their head of household is (%(hhhh)s). " \
                                  ) % \
                                  {'hh': death.household, \
                                   'hhhh': death.household.household})

        death_check = DeadPerson.objects.filter( \
                                first_name__iexact=death.first_name, \
                                last_name__iexact=death.last_name, \
                                dob=death.dob)

        if len(death_check) > 0:
            old_p = death_check[0]
            if old_p.chw == chw:
                death_chw = _(u"you")
            else:
                death_chw = death_check[0].chw
            raise BadValue(_(u"%(name)s %(sex)s/%(age)s was already " \
                              "reported by %(chw)s. ") % \
                              {'name': old_p.full_name(), \
                               'sex': old_p.gender, \
                               'age': old_p.humanised_age(), \
                               'chw': death_chw})
        death.save()

        self.message.respond(_("You successfuly reported the death of "\
                                "%(death)s.") % {'death': death})
        return True

