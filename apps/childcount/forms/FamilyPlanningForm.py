#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import FamilyPlanningReport
from childcount.models import CodedItem, FamilyPlanningUsage, Encounter
from childcount.exceptions import ParseError


class FamilyPlanningForm(CCForm):
    KEYWORDS = {
        'en': ['k', 'fp'],
        'fr': ['k', 'fp'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: | number of women " \
                                "aged 15 - 49 | number using FP | methods " \
                                "being used |"))

        try:
            fpr = FamilyPlanningReport.objects.get(encounter=self.encounter)
        except FamilyPlanningReport.DoesNotExist:
            fpr = FamilyPlanningReport(encounter=self.encounter)
        else:
            for usage in fpr.familyplanningusage_set.all():
                usage.delete()
            fpr.reset()
        fpr.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of women aged 15 - 49 | must be " \
                                "entered as a number."))

        fpr.women = int(self.params[1])
        if fpr.women == 0:
            self.response = _(u"No women aged 15 - 49 visited.")
            fpr.save()
            return

        if len(self.params) < 3:
            raise ParseError(_(u"After entering the number of women aged " \
                               "15-49, you must indicate how many use " \
                               "modern family planning methods."))

        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of women using modern family " \
                                "planning methods must be entered as " \
                                "a number."))
        fpr.women_using = int(self.params[2])

        if fpr.women_using > fpr.women:
            raise BadValue(_(u"The number of women using family planning " \
                              "can not be greater than the total number of " \
                              "women."))
        if fpr.women_using == 0:
            self.response = _(u"%(women)d women aged 15-49, none using " \
                               "modern family planning.") % \
                               {'women': fpr.women}
            fpr.save()
            return

        if len(self.params[3:]) < fpr.women_using:
            raise ParseError(_(u"You must specify %(num)d family planning " \
                                "methods code(s). One for each of the " \
                                "%(num)s women " \
                                "using modern family planning.") % \
                                {'num': fpr.women_using})

        methods = dict([(method.local_code.lower(), method) \
                             for method in \
                             CodedItem.objects.filter(\
                                type=CodedItem.TYPE_FAMILY_PLANNING)])
        valid = []
        unkown = []
        for d in self.params[3:]:
            obj = methods.get(d, None)
            if obj is not None:
                valid.append(obj)
            else:
                unkown.append(d)

        if unkown:
            invalid_str = _(u"Unkown family planning code(s): %(codes)s " \
                          "No family planning recorded.") % \
                         {'codes': ', '.join(unkown).upper()}
            raise ParseError(invalid_str)

        if valid:
            fpr.save()
            fp_strings = []
            for method in methods.values():
                if valid.count(method) > 0:
                    count = valid.count(method)
                    FamilyPlanningUsage(fp_report=fpr, method=method, \
                                        count=count).save()
                    fp_strings.append('%s (%d)' % (method.description, count))

            fp_string = ', '.join(fp_strings)
            self.response = _(u"%(women)d women, %(using)d using family " \
                               "planning: %(fp_string)s") % \
                               {'women': fpr.women, 'using': fpr.women_using, \
                                'fp_string': fp_string}
