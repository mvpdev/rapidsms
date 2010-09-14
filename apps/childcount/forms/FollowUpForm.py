#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.models import Encounter
from childcount.models.reports import FollowUpReport
from childcount.forms.utils import MultipleChoiceField


class FollowUpForm(CCForm):
    KEYWORDS = {
        'en': ['u'],
        'fr': ['u'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):

        imp_field = MultipleChoiceField()
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_YES, 'Y')
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_NO, 'N')
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_UNKOWN, 'U')
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_UNAVAILABLE, 'L')

        v_field = MultipleChoiceField()
        v_field.add_choice('en', FollowUpReport.VISITED_YES, 'Y')
        v_field.add_choice('en', FollowUpReport.VISITED_NO, 'N')
        v_field.add_choice('en', FollowUpReport.VISITED_UNKOWN, 'U')
        v_field.add_choice('en', FollowUpReport.VISITED_INPATIENT, 'P')

        try:
            fur = FollowUpReport.objects.get(encounter=self.encounter)
            fur.reset()
        except FollowUpReport.DoesNotExist:
            fur = FollowUpReport(encounter=self.encounter)
        fur.form_group = self.form_group

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: " \
                                "| Improvement? | Visited facility? | "))

        imp_field.set_language(self.chw.language)
        imp = self.params[1]
        if not imp_field.is_valid_choice(imp):
            raise BadValue(_(u"| Improvement? | Must be " \
                              "%(choices)s.") % \
                              {'choices': imp_field.choices_string()})
        imp_db = imp_field.get_db_value(imp)

        v_field.set_language(self.chw.language)
        v = self.params[2]
        if not v_field.is_valid_choice(v):
            raise BadValue(_(u"| Visited facility? | Must be " \
                              "%(choices)s.") % \
                              {'choices': v_field.choices_string()})
        v_db = v_field.get_db_value(v)

        if imp_db == FollowUpReport.IMPROVEMENT_YES:
            imp_string = _(u"Condition improved.")
        elif imp_db == FollowUpReport.IMPROVEMENT_NO:
            imp_string = _(u"Condition did not improve.")
        elif imp_db == FollowUpReport.IMPROVEMENT_UNKOWN:
            imp_string = _(u"Condition improvement unkown.")
        elif imp_db == FollowUpReport.IMPROVEMENT_UNAVAILABLE:
            imp_string = _(u"Patient unavailable.")

        if v_db == FollowUpReport.VISITED_YES:
            v_string = _(u"Patient visited health facility.")
        elif v_db == FollowUpReport.VISITED_NO:
            v_string = _(u"Patient did not visit health facility.")
        elif v_db == FollowUpReport.VISITED_UNKOWN:
            v_string = _(u"Unknown if patient visited health facility.")
        elif v_db == FollowUpReport.VISITED_INPATIENT:
            v_string = _(u"Patient currently inpatient at health facility.")

        self.response = imp_string + ', ' + v_string

        fur.improvement = imp_db
        fur.visited_clinic = v_db

        fur.save()
