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

        #share status choice
        share_field = MultipleChoiceField()
        share_field.add_choice('en', SanitationReport.SHARE_YES, 'Y')
        share_field.add_choice('en', SanitationReport.SHARE_NO, 'N')
        share_field.add_choice('en', SanitationReport.SHARE_UNKOWN, 'U')

        try:
            snr = SanitationReport.objects.get(encounter=self.encounter)
            snr.reset()
        except SanitationReport.DoesNotExist:
            snr = SanitationReport(encounter=self.encounter)

        snr.form_group = self.form_group

        sanit_field.set_language(self.chw.language)
        share_field.set_language(self.chw.language)

        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. What kind of toilet " \
                                "facility do members of your household " \
                                "use | do you share?"))

        toilet_latrine = self.params[1]
        if not sanit_field.is_valid_choice(toilet_latrine):
            raise ParseError(_(u"| Toilet type | must be %(choices)s.") \
                             % {'choices': sanit_field.choices_string()})

        snr.toilet_lat = sanit_field.get_db_value(toilet_latrine)

        share_toilet = self.params[2]
        if not share_field.is_valid_choice(share_toilet):
            raise ParseError(_(u"|Do you share toilet?| must be " \
                                "%(choices)s.") % \
                                {'choices': share_field.choices_string()})
        share_toilet = share_field.get_db_value(share_toilet)

        snr.share_toilet = share_toilet

        snr.save()
