#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import SanitationReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class SanitationForm(CCForm):
    KEYWORDS = {
        'en': ['san'],
        'fr': ['san'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #Sanitation type source field
        sanit_field = MultipleChoiceField()
        sanit_field.add_choice('en', SanitationReport.FLUSH, 'FL')
        sanit_field.add_choice('en', \
                                SanitationReport.VENTILATED_IMPROVED_PIT, 'VP')
        sanit_field.add_choice('en', SanitationReport.PITLAT_WITH_SLAB, 'PN')
        sanit_field.add_choice('en', SanitationReport.PITLAT_WITHOUT_SLAB, \
                                    'PY')
        sanit_field.add_choice('en', SanitationReport.COMPOSTING_TOILET, 'CT')
        sanit_field.add_choice('en', SanitationReport.BUCKET, 'BT')
        sanit_field.add_choice('en', SanitationReport.HANGING_TOILET_LAT, 'HT')
        sanit_field.add_choice('en', SanitationReport.NO_FACILITY_OR_BUSH, \
                                     'NS')
        sanit_field.add_choice('en', SanitationReport.OTHER, 'Z')

        sanit_share = MultipleChoiceField()
        sanit_share.add_choice('en', SanitationReport.PB, 'PB')
        sanit_share.add_choice('en', SanitationReport.U, 'U')

        try:
            snr = SanitationReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
            snr.reset()
        except SanitationReport.DoesNotExist:
            snr = SanitationReport(encounter=self.encounter)

        snr.form_group = self.form_group

        sanit_field.set_language(self.chw.language)
        sanit_share.set_language(self.chw.language)

        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: | kind of " \
                                "toilet facility | how many share? |"))

        toilet_latrine = self.params[1]
        if not sanit_field.is_valid_choice(toilet_latrine):
            raise ParseError(_(u"| Toilet type | must be %(choices)s.") \
                             % {'choices': sanit_field.choices_string()})

        snr.toilet_lat = sanit_field.get_db_value(toilet_latrine)

        share_toilet = self.params[2]
        if share_toilet.isdigit():
            snr.share_toilet = int(share_toilet)
        elif sanit_share.is_valid_choice(share_toilet):
            snr.share_toilet = sanit_share.get_db_value(share_toilet)
        else:
            raise ParseError(_(u"| Do you share toilet? | must be a number " \
                                "or %(choices)s.") % \
                                {'choices': sanit_share.choices_string()})

        snr.save()

        self.response = _(u"Primary Sanitation: %(san)s Share: %(share)s ") % \
                           {'san': snr.toilet_lat, 'share': self.params[2]}
