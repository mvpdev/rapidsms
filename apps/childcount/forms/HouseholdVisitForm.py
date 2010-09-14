#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import HouseholdVisitReport
from childcount.models import CodedItem, Encounter
from childcount.forms.utils import MultipleChoiceField
from childcount.exceptions import ParseError


class HouseholdVisitForm(CCForm):
    KEYWORDS = {
        'en': ['v'],
        'fr': ['v'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):

        available_field = MultipleChoiceField()
        available_field.add_choice('en', True, 'Y')
        available_field.add_choice('en', False, 'N')

        try:
            hhvr = HouseholdVisitReport.objects.get(encounter=self.encounter)
        except HouseholdVisitReport.DoesNotExist:
            hhvr = HouseholdVisitReport(encounter=self.encounter)
        hhvr.form_group = self.form_group

        available_field.set_language(self.chw.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: | household " \
                                "member " \
                                "available? | number of children | " \
                                "counseling / advice given (optional) |"))
        if not available_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"| Any HH Member Available? | must be "\
                               "%(choices)s.") % \
                              {'choices': available_field.choices_string()})

        available = available_field.get_db_value(self.params[1])

        hhvr.available = available

        if available:
            if len(self.params) < 3:
                raise ParseError(_(u"Not enough info. Expected: | household " \
                                "member available? | number of children | " \
                                "counseling / advice given (optional) |"))

            if not self.params[2].isdigit():
                raise ParseError(_("| Number of children | must be entered as " \
                                   "a number."))

            children = int(self.params[2])
            hhvr.children = children

            if len(self.params) > 3:
                topics = dict([(counseling.local_code.lower(), counseling) \
                                 for counseling in \
                                 CodedItem.objects.filter(\
                                    type=CodedItem.TYPE_COUNSELING)])
                valid = []
                unkown = []
                for d in self.params[3:]:
                    obj = topics.get(d, None)
                    if obj is not None:
                        valid.append(obj)
                    else:
                        unkown.append(d)

                if unkown:
                    invalid_str = _(u"Unknown counseling topic code(s): " \
                                     "%(codes)s No household visit " \
                                     "recorded.") % \
                                     {'codes': ', '.join(unkown).upper()}
                    raise ParseError(invalid_str)

                hhvr.save()
                for topic in valid:
                    hhvr.counseling.add(topic)

        hhvr.save()

        if not available:
            self.response = _(u"Household member not available.")
            return

        if available:
            self.response = _(u"Household member available, %(kids)d " \
                               "children under 5 seen.") % \
                                                      {'kids': hhvr.children}
            if hhvr.counseling.count() > 0:
                self.response += _(u", counseling / advice topics covered: " \
                                    "%(topics)s") % {'topics': ', '.join( \
                           [topic.description for topic in \
                                                    hhvr.counseling.all()])}
