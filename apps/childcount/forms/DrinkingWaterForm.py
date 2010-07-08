#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import DrinkingWaterReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class DrinkingWaterForm(CCForm):
    KEYWORDS = {
        'en': ['dw'],
        'fr': ['dw'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #Water source field
        wats_field = MultipleChoiceField()
        wats_field.add_choice('en', DrinkingWaterReport.PIPED_WATER, 'PP')
        wats_field.add_choice('en', DrinkingWaterReport.PUBLIC_TAP_STANDPIPE, \
                                    'PT')
        wats_field.add_choice('en', DrinkingWaterReport.TUBEWELL_BOREHOLE, \
                                    'TB')
        wats_field.add_choice('en', DrinkingWaterReport.PROTECTED_DUG_WELL, \
                                    'PW')
        wats_field.add_choice('en', DrinkingWaterReport.UNPROTECTED_DUG_WELL, \
                                    'UW')
        wats_field.add_choice('en', DrinkingWaterReport.PROTECTED_SPRING, 'PS')
        wats_field.add_choice('en', DrinkingWaterReport.UNPROTECTED_SPRING, \
                                    'UP')
        wats_field.add_choice('en', DrinkingWaterReport.RAIN_COLLECTION, 'RW')
        wats_field.add_choice('en', DrinkingWaterReport.SURFACE_WATER, 'SU')
        wats_field.add_choice('en', DrinkingWaterReport.OTHER, 'Z')

        #treatment status choice
        treat_field = MultipleChoiceField()
        treat_field.add_choice('en', DrinkingWaterReport.TREAT_YES, 'Y')
        treat_field.add_choice('en', DrinkingWaterReport.TREAT_NO, 'N')
        treat_field.add_choice('en', DrinkingWaterReport.TREAT_UNKOWN, 'U')

        #method used
        tmethod_field = MultipleChoiceField()
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                        TREATMENT_METHOD_BOIL, 'BW')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_ADDBLEACH_CHLORINE, 'AC')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_CLOTH, 'SC')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_WATERFILTER, 'WF')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_SOLARDISINFECTION, 'SR')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_STAND_SETTLE, 'LS')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_OTHER, 'Z')
        tmethod_field.add_choice('en', DrinkingWaterReport. \
                                    TREATMENT_METHOD_DONTKNOW, 'U')

        try:
            drnkr = DrinkingWaterReport.objects.get(encounter=self.encounter)
            drnkr.reset()
        except DrinkingWaterReport.DoesNotExist:
            drnkr = DrinkingWaterReport(encounter=self.encounter)

        drnkr.form_group = self.form_group

        wats_field.set_language(self.chw.language)
        treat_field.set_language(self.chw.language)
        tmethod_field.set_language(self.chw.language)

        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. What is source of water  " \
                                "do you treat | what do u use to treat"))

        wats = self.params[1]
        if not wats_field.is_valid_choice(wats):
            raise ParseError(_(u"|Water Source| must be %(choices)s.") \
                             % {'choices': wats_field.choices_string()})

        drnkr.water_source = wats_field.get_db_value(wats)

        treat = self.params[2]
        if not treat_field.is_valid_choice(treat):
            raise ParseError(_(u"|Do you treat water?| must be " \
                                "%(choices)s.") % \
                                {'choices': treat_field.choices_string()})
        treat_water = treat_field.get_db_value(treat)

        drnkr.treat_water = treat_water

        if treat_water in (DrinkingWaterReport.TREAT_YES):
            if len(self.params) < 3:
                raise ParseError(_(u"Not enough info. Expected: " \
                                    "Method used to treat water "))

            if not tmethod_field.is_valid_choice(self.params[3]):
                raise ParseError(_(u"|Which method do you use?| must be " \
                                "%(choices)s.") % \
                                {'choices': tmethod_field.choices_string()})

            method_used = tmethod_field.get_db_value(self.params[3])

        drnkr.treatment_method = method_used
        drnkr.save()
