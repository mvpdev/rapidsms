#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import ExtendedSanitationReport as SanitationReport
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class ExtendedSanitationForm(CCForm):
    """ Sanitation Form

    Params:
        * type (FL/VP/PY/PN/CT/HT/BT/NS/Z)
        * share_toilet (int)
        * Hand Wash Facility
        * Wash hand with
        * Have Shower/Bathroom
        
    """

    KEYWORDS = {
        'en': ['san'],
        'rw': ['san'],
        'fr': ['san'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #Sanitation type source field
        sanit_field = MultipleChoiceField()
        sanit_field.add_choice('en', SanitationReport.FLUSH, 'FL')
        sanit_field.add_choice('en', \
                                SanitationReport.VENTILATED_IMPROVED_PIT, 'VP')
        sanit_field.add_choice('en', SanitationReport.PITLAT_WITH_SLAB, 'PY')
        sanit_field.add_choice('en', SanitationReport.PITLAT_WITHOUT_SLAB, \
                                    'PN')
        sanit_field.add_choice('en', SanitationReport.COMPOSTING_TOILET, 'CT')
        sanit_field.add_choice('en', SanitationReport.BUCKET, 'BT')
        sanit_field.add_choice('en', SanitationReport.HANGING_TOILET_LAT, 'HT')
        sanit_field.add_choice('en', SanitationReport.NO_FACILITY_OR_BUSH, \
                                     'NS')
        sanit_field.add_choice('en', SanitationReport.OTHER, 'Z')
        sanit_field.add_choice('rw', SanitationReport.FLUSH, 'FL')
        sanit_field.add_choice('rw', \
                                SanitationReport.VENTILATED_IMPROVED_PIT, 'VP')
        sanit_field.add_choice('rw', SanitationReport.PITLAT_WITH_SLAB, 'PY')
        sanit_field.add_choice('rw', SanitationReport.PITLAT_WITHOUT_SLAB, \
                                    'PN')
        sanit_field.add_choice('rw', SanitationReport.COMPOSTING_TOILET, 'CT')
        sanit_field.add_choice('rw', SanitationReport.BUCKET, 'BT')
        sanit_field.add_choice('rw', SanitationReport.HANGING_TOILET_LAT, 'HT')
        sanit_field.add_choice('rw', SanitationReport.NO_FACILITY_OR_BUSH, \
                                     'NS')
        sanit_field.add_choice('rw', SanitationReport.OTHER, 'Z')
        sanit_field.add_choice('fr', SanitationReport.FLUSH, 'FL')
        sanit_field.add_choice('fr', \
                                SanitationReport.VENTILATED_IMPROVED_PIT, 'VP')
        sanit_field.add_choice('fr', SanitationReport.PITLAT_WITH_SLAB, 'PN')
        sanit_field.add_choice('fr', SanitationReport.PITLAT_WITHOUT_SLAB, \
                                    'PY')
        sanit_field.add_choice('fr', SanitationReport.COMPOSTING_TOILET, 'CT')
        sanit_field.add_choice('fr', SanitationReport.BUCKET, 'BT')
        sanit_field.add_choice('fr', SanitationReport.HANGING_TOILET_LAT, 'HT')
        sanit_field.add_choice('fr', SanitationReport.NO_FACILITY_OR_BUSH, \
                                     'NS')
        sanit_field.add_choice('fr', SanitationReport.OTHER, 'Z')

        sanit_share = MultipleChoiceField()
        sanit_share.add_choice('en', SanitationReport.SHARE_YES, 'Y')
        sanit_share.add_choice('en', SanitationReport.SHARE_NO, 'N')
        sanit_share.add_choice('en', SanitationReport.SHARE_UNKNOWN, 'U')
        sanit_share.add_choice('rw', SanitationReport.SHARE_YES, 'Y')
        sanit_share.add_choice('rw', SanitationReport.SHARE_NO, 'N')
        sanit_share.add_choice('rw', SanitationReport.SHARE_UNKNOWN, 'U')
        sanit_share.add_choice('fr', SanitationReport.SHARE_YES, 'Y')
        sanit_share.add_choice('fr', SanitationReport.SHARE_NO, 'N')
        sanit_share.add_choice('fr', SanitationReport.SHARE_UNKNOWN, 'U')


        handwash_facility = MultipleChoiceField()
        handwash_facility.add_choice('en', SanitationReport.FACILITY_YES, 'Y')
        handwash_facility.add_choice('en', SanitationReport.FACILITY_NO, 'N')
        handwash_facility.add_choice('en', SanitationReport.FACILITY_UNKNOWN, 'U')
        handwash_facility.add_choice('rw', SanitationReport.FACILITY_YES, 'Y')
        handwash_facility.add_choice('rw', SanitationReport.FACILITY_NO, 'N')
        handwash_facility.add_choice('rw', SanitationReport.FACILITY_UNKNOWN, 'U')
        handwash_facility.add_choice('fr', SanitationReport.FACILITY_YES, 'Y')
        handwash_facility.add_choice('fr', SanitationReport.FACILITY_NO, 'N')
        handwash_facility.add_choice('fr', SanitationReport.FACILITY_UNKNOWN, 'U')
        
        wash_handwith = MultipleChoiceField()
        wash_handwith.add_choice('en', SanitationReport.USE_SOAP, 'S')
        wash_handwith.add_choice('en', SanitationReport.USE_ASH, 'AS')
        wash_handwith.add_choice('en', SanitationReport.USE_WATER, 'OWR')
        wash_handwith.add_choice('rw', SanitationReport.USE_SOAP, 'S')
        wash_handwith.add_choice('rw', SanitationReport.USE_ASH, 'AS')
        wash_handwith.add_choice('rw', SanitationReport.USE_WATER, 'OWR')
        wash_handwith.add_choice('fr', SanitationReport.USE_SOAP, 'S')
        wash_handwith.add_choice('fr', SanitationReport.USE_ASH, 'AS')
        wash_handwith.add_choice('fr', SanitationReport.USE_WATER, 'OWR')
        
        shower_facility = MultipleChoiceField()
        shower_facility.add_choice('en', SanitationReport.FACILITY_YES, 'Y')
        shower_facility.add_choice('en', SanitationReport.FACILITY_NO, 'N')
        shower_facility.add_choice('en', SanitationReport.FACILITY_UNKNOWN, 'U')
        shower_facility.add_choice('rw', SanitationReport.FACILITY_YES, 'Y')
        shower_facility.add_choice('rw', SanitationReport.FACILITY_NO, 'N')
        shower_facility.add_choice('rw', SanitationReport.FACILITY_UNKNOWN, 'U')
        shower_facility.add_choice('fr', SanitationReport.FACILITY_YES, 'Y')
        shower_facility.add_choice('fr', SanitationReport.FACILITY_NO, 'N')
        shower_facility.add_choice('fr', SanitationReport.FACILITY_UNKNOWN, 'U')

        try:
            snr = SanitationReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
            snr.reset()
        except SanitationReport.DoesNotExist:
            snr = SanitationReport(encounter=self.encounter)

        snr.form_group = self.form_group

        sanit_field.set_language(self.chw.language)
        sanit_share.set_language(self.chw.language)
        shower_facility.set_language(self.chw.language)
        handwash_facility.set_language(self.chw.language)
        wash_handwith.set_language(self.chw.language)
        
        if len(self.params) < 6:
            raise ParseError(_(u"Not enough info. Expected: | kind of " \
                                "toilet facility | how many share? |"))

        toilet_latrine = self.params[1]
        if not sanit_field.is_valid_choice(toilet_latrine):
            raise ParseError(_(u"| Toilet type | must be %(choices)s.") \
                             % {'choices': sanit_field.choices_string()})

        snr.toilet_lat = sanit_field.get_db_value(toilet_latrine)

        share_toilet = self.params[2]
        if not sanit_share.is_valid_choice(share_toilet):
            raise ParseError(_(u"| Do you share toilet? | must be %s.") \
                                    % sanit_share.choices_string())

        snr.share_toilet = sanit_share.get_db_value(share_toilet)
        
        handwashfacility = self.params[3]
        if not handwash_facility.is_valid_choice(handwashfacility):
            raise ParseError(_(u"| Is there hand washing facility? | " \
                                "must be %s.") % \
                                    handwash_facility.choices_string())

        snr.handwash_facility = handwash_facility.get_db_value(handwashfacility)
                                        
        washhandwith = self.params[4]
        if not wash_handwith.is_valid_choice(washhandwith):
            raise ParseError(_(u"| What do they wash hand with? | must " \
                                "be %s.") % wash_handwith.choices_string())
        snr.wash_handwith = wash_handwith.get_db_value(washhandwith)

        shower = self.params[5]
        if not shower_facility.is_valid_choice(shower):
            raise ParseError(_(u"| Is there shower?  | must be %s.") \
                                    % shower_facility.choices_string())
        snr.shower = shower_facility.get_db_value(shower)
    
        snr.save()

        self.response = _(u"Primary Sanitation: %(san)s Share: %(share)s ") % \
                           {'san': snr.toilet_lat, 'share': self.params[2]}
