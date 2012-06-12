#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin
import re

from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group

from CCForm import CCForm
from childcount.models import Encounter
from childcount.models.reports import NutritionReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField
from childcount.utils import alert_health_team, alert_nutrition_team


class NutritionForm(CCForm):
    """ Nutrition Form

    Params:
        * MPB (int)
        * Oed (Y/N/U)
        * Kg (optional)
    """

    KEYWORDS = {
        'en': ['m', 'muac'],
        'rw': ['m', 'muac'],
        'fr': ['m', 'muac'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    WEIGHT_UNIT = 'kg'

    MAX_WEIGHT = 100
    MIN_WEIGHT = 3
    MAX_MUAC = 250
    MIN_MUAC = 50

    def process(self, patient):
        oedema_field = MultipleChoiceField()
        oedema_field.add_choice('en', NutritionReport.OEDEMA_YES, 'Y')
        oedema_field.add_choice('en', NutritionReport.OEDEMA_NO, 'N')
        oedema_field.add_choice('en', NutritionReport.OEDEMA_UNKNOWN, 'U')
        oedema_field.add_choice('rw', NutritionReport.OEDEMA_YES, 'Y')
        oedema_field.add_choice('rw', NutritionReport.OEDEMA_NO, 'N')
        oedema_field.add_choice('rw', NutritionReport.OEDEMA_UNKNOWN, 'U')
        oedema_field.add_choice('fr', NutritionReport.OEDEMA_YES, 'O')
        oedema_field.add_choice('fr', NutritionReport.OEDEMA_NO, 'N')
        oedema_field.add_choice('fr', NutritionReport.OEDEMA_UNKNOWN, 'I')
        keyword = self.params[0]

        try:
            nr = NutritionReport.objects.get(encounter=self.encounter)
            nr.reset()
        except NutritionReport.DoesNotExist:
            nr = NutritionReport(encounter=self.encounter)
        nr.form_group = self.form_group

        days, weeks, months = patient.age_in_days_weeks_months(\
            self.encounter.encounter_date.date())

        if months < 6:
            raise Inapplicable(_(u"Child is too young for MUAC."))
        elif months > 59:
            raise Inapplicable(_(u"Child is older than 59 months. If there " \
                                  "are any concerns about the child, " \
                                  "please refer to a clinic."))

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: | muac | oedema " \
                                "| weight (optional) |"))

        if not self.params[1].isdigit():
            raise ParseError(_(u"| MUAC | must be entered as a number."))

        muac = int(self.params[1])
        if muac == 0:
            muac = None
            if len(self.params) < 4:
                raise ParseError(\
                            _(u"Not enough info. Expected: | muac | oedema " \
                                    "| weight (mandatory) |"))
        elif muac < self.MIN_MUAC:
            raise BadValue(_(u"MUAC too low. If correct, refer child to " \
                             "clinic IMMEDIATELY!"))
        elif muac > self.MAX_MUAC:
            raise BadValue(_(u"MUAC too high. Correct and resend."))

        oedema_field.set_language(self.chw.language)

        if not oedema_field.is_valid_choice(self.params[2]):
            raise ParseError(_(u"| Oedema | must be " \
                                "%(choices)s.") % \
                               {'choices': oedema_field.choices_string()})

        oedema_db = oedema_field.get_db_value(self.params[2])

        weight = None
        if len(self.params) > 3:
            regex = r'(?P<w>\d+(\.?\d*)?).*'
            match = re.match(regex, self.params[3])
            if match:
                weight = float(match.groupdict()['w'])
                if weight > self.MAX_WEIGHT:
                    raise BadValue(_(u"Weight can not be greater than " \
                                      "%(max)skg.") % \
                                     {'max': self.MAX_WEIGHT})
                if weight < self.MIN_WEIGHT:
                    raise BadValue(_(u"Weight can not be less than " \
                                      "%(min)skg.") % \
                                     {'min': self.MIN_WEIGHT})
            else:
                raise ParseError(_(u"Unkown value. Weight should be " \
                                    "entered as a number."))

        nr.oedema = oedema_db
        nr.muac = muac
        nr.weight = weight
        nr.save()

        if muac is None:
            self.response = _(u"MUAC not taken, ")
        else:
            self.response = _(u"MUAC of %(muac)smm, ") % {'muac': muac}

        if oedema_db == NutritionReport.OEDEMA_YES:
            self.response += _(u"Oedema present.")
        elif oedema_db == NutritionReport.OEDEMA_NO:
            self.response += _(u"No signs of oedema.")
        elif oedema_db == NutritionReport.OEDEMA_UNKNOWN:
            self.response += _(u"Oedema unkown.")

        if weight is not None:
            self.response += _(u", Weight %(w)skg") % {'w': weight}
        if nr.status == NutritionReport.STATUS_SEVERE_COMP:
            status_msg = _(u"SAM+")
        elif nr.status == NutritionReport.STATUS_MODERATE:
            status_msg = _(u"MAM")
        elif nr.status == NutritionReport.STATUS_SEVERE:
            status_msg = _(u"SAM")
        else:
            status_msg = _(u"HEALTHY")
        self.response = status_msg + "> " + self.response
        if nr.status in (NutritionReport.STATUS_SEVERE, \
                            NutritionReport.STATUS_SEVERE_COMP):
            if nr.status == NutritionReport.STATUS_SEVERE_COMP:
                status_msg = _(u"SAM+")
            else:
                status_msg = _(u"SAM")
            msg = _(u"%(status)s>%(child)s, %(location)s has %(status)s. " \
                    "%(msg)s CHW no: %(mobile)s") % {'child': patient, \
                        'location': patient.location, 'status': status_msg, \
                        'mobile': self.chw.connection().identity, \
                        'msg': self.response}
            #alert facilitators
            alert_health_team('malnutrition', msg)
            #alert nutritionists
            alert_nutrition_team('malnutrition', msg)
