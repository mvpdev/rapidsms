#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import BednetUtilization
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class BednetUtilizationForm(CCForm):
    KEYWORDS = {
        'en': ['bu'],
        'fr': ['bu'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        reason_field = MultipleChoiceField()
        reason_field.add_choice('en', BednetUtilization.DONT_HAVE, 'NH')
        reason_field.add_choice('en', BednetUtilization.BEDNET_DAMAGED, 'BD')
        reason_field.add_choice('en', BednetUtilization.DIFFICULT_HUNG, 'DH')
        reason_field.add_choice('en', BednetUtilization.SMALL_ROOM, 'SR')
        reason_field.add_choice('en', BednetUtilization.DIFFICULT_BREATHE, \
                                'DB')
        reason_field.add_choice('en', BednetUtilization.NOT_EFFECTIVE, 'NE')
        reason_field.add_choice('en', BednetUtilization.OTHER, 'Z')
        reason_field.add_choice('en', BednetUtilization.UNKNOWN, 'U')

        hanging_field = MultipleChoiceField()
        hanging_field.add_choice('en', BednetUtilization.U, 'U')

        if len(self.params) < 4:
            raise ParseError(_(u"Not enough info. Expected: | number of " \
                                "children who slept here last night | "\
                                " how many slept under bednets | hanging " \
                                "bednets |"))

        try:
            bnut_rpt = BednetUtilization.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except BednetUtilization.DoesNotExist:
            bnut_rpt = BednetUtilization(encounter=self.encounter)
            overwrite = False
        else:
            bnut_rpt.reset()
            overwrite = True

        bnut_rpt.form_group = self.form_group
        reason_field.set_language(self.chw.language)
        hanging_field.set_language(self.chw.language)

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of children who slept here last" \
                                " night | should be a number."))

        bnut_rpt.child_underfive = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of children under bednet | should " \
                                "be a number."))

        bnut_rpt.child_lastnite = int(self.params[2])

        if bnut_rpt.child_lastnite > bnut_rpt.child_underfive:
            raise ParseError(_(u"Number of under five who slept here last " \
                                "night should be more than those who slept " \
                                "under bednet"))

        hanging = self.params[3]
        if hanging.isdigit():
            bnut_rpt.hanging_bednet = hanging
        elif hanging_field.is_valid_choice(hanging):
            bnut_rpt.hanging_bednet = hanging_field.get_db_value(hanging)
        else:
            raise ParseError(_(u"| How many hanging bednet | must be a number" \
                                " or, %(choices)s.") % \
                                {'choices': hanging_field.choices_string()})

        self.response = _(u"%(sites)d child(ren) slept here last night. " \
                           "%(nets)d slept under bednet(s). Hanging: " \
                           "%(han)s") % \
                           {'sites': bnut_rpt.child_underfive, \
                            'nets': bnut_rpt.child_lastnite, \
                            'han': self.params[3]}

        num = int(self.params[1]) - int(self.params[2])
        if num > 0:
            if len(self.params) > 4:
                reason = self.params[4]
                if not reason_field.is_valid_choice(reason):
                    raise ParseError(_(u"| Reason | must be " \
                                        "%(choices)s.") % \
                                        {'choices': \
                                        reason_field.choices_string()})

                bnut_rpt.reason = reason_field.get_db_value(reason)
                self.response += _(u" Reason: %(reason)s ") % \
                                    {'reason': bnut_rpt.reason}
            else:
                raise ParseError(_(u" You must state the reason why children" \
                                    " never slept under bednet"))

        bnut_rpt.save()
