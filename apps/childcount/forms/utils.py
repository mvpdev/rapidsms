#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


import itertools

from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict


class MultipleChoiceField(object):

        def __init__(self):
            self.choices = {}
            self.active_language = None

        def add_choice(self, language, db_value, choices):
            if language not in self.choices:
                self.choices[language] = SortedDict()
            if not isinstance(choices, list):
                choices = [choices]
            self.choices[language][db_value] = choices

        def set_language(self, language):
            self.active_language = language

        def is_valid_choice(self, choice):
            return choice.lower() in self.valid_choices()

        def valid_choices(self):
            return [char.lower() for char in \
                itertools.chain(*self.choices[self.active_language].values())]

        def propper_answer(self, choice):
            if not self.is_valid_choice(choice):
                return None
            return self.choices[self.active_language] \
                                    [self.get_db_value(choice)][0].upper()

        def choices_string(self):
            choices = []
            for key, value in self.choices[self.active_language].iteritems():
                choices.append(value[0].upper())
            if len(choices) == 1:
                return choices[0]
            if len(choices) == 2:
                return _(u" or ").join(choices)
            else:
                return _(u"%(choices)s, or %(lastchoice)s") \
                       % {'choices': ', '.join(choices[:-1]), \
                          'lastchoice': choices[-1]}

        def get_db_value(self, choice):
            if not self.is_valid_choice(choice):
                return None
            for key, value in self.choices[self.active_language].iteritems():
                if choice in [char.lower() for char in value]:
                    return key
