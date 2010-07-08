#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin
import re

from django.utils.translation import ugettext as _

from CCForm import CCForm
from childcount.models import Encounter
from childcount.models.reports import NutritionReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class NutritionForm(CCForm):
    KEYWORDS = {
        'en': ['m', 'muac'],
        'fr': ['m', 'muac'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    WEIGHT_UNIT = 'kg'

    MAX_WEIGHT = 100
    MIN_WEIGHT = 3

    def process(self, patient):
        oedema_field = MultipleChoiceField()
        oedema_field.add_choice('en', NutritionReport.OEDEMA_YES, 'Y')
        oedema_field.add_choice('en', NutritionReport.OEDEMA_NO, 'N')
        oedema_field.add_choice('en', NutritionReport.OEDEMA_UNKOWN, 'U')
        keyword = self.params[0]

        try:
            nr = NutritionReport.objects.get(encounter=self.encounter)
            nr.reset()
        except NutritionReport.DoesNotExist:
            nr = NutritionReport(encounter=self.encounter)
        nr.form_group = self.form_group

        days, weeks, months = patient.age_in_days_weeks_months()

        if days <= 30:
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
        elif muac < 50:
            raise BadValue(_(u"MUAC too low. If correct, refer child to " \
                             "clinic IMMEDIATELY!"))
        elif muac > 250:
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
                raise ParseError(_(u"Unkown value. Weight should be entered as a number."))

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
        elif oedema_db == NutritionReport.OEDEMA_UNKOWN:
            self.response += _(u"Oedema unkown.")

        if weight is not None:
            self.response += _(", Weight %(w)skg") % {'w': weight}

        #TODO Referral / Case
        '''
        if mr.status == NutritionReport.STATUS_SEVERE:
            info = {}
            info.update({'last_name': patient.last_name,
                         'first_name': patient.first_name,
                         'age': patient.age(),
                         'zone': patient.zone})
            rf = Referral(patient=patient)
            info.update({'refid': rf.referral_id})

            expires_on = datetime.now() + timedelta(15)
            case = Case(patient=patient, expires_on=expires_on)
            case.save()

            response = _('SAM> Last, First (AGE) LOCATION has acute '\
                     'malnutrition. Please refer child to clinic '\
                     'IMMEDIATELY. (%(refid)s')
            #setup alert
            # SAM> Last, First (AGE), LOCATION has SAM. CHW NAME -
            #CHWMOBILE. (REFID)
        '''
