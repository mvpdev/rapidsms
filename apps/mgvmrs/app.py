#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from datetime import datetime

import rapidsms

from mgvmrs.forms import *
from mgvmrs.utils import *


class App (rapidsms.app.App):
    ''' demo App only

    demonstrates how to use the OMRS link '''

    def handle(self, message):
        # debug only.
        if message.text.startswith('omrs'):
            dt = datetime.now()
            infos = message.text.split(" ")
            mri = infos[1]

            individual = OpenMRSConsultationForm(create=True, mri=mri, location=1, \
                            provider=1, encounter_datetime=dt, dob=datetime.today(), \
                            dob_estimate=False, family_name='smith', given_name='joe',
                            sex='M')

            individual.assign('visit_to_health_facility_since_last_home_visit', \
                        individual.NO)
            individual.assign('patients_condition_improved', \
                        individual.NO)
            individual.assign('danger_signs_present', individual.YES)
            individual.assign('month_of_current_gestation', 2)
            individual.assign('antenatal_visit_number', 4)
            individual.assign('weeks_since_last_anc', 2)
            individual.assign('number_of_health_facility_visits_since_birth', 1)
            individual.assign('breastfed_exclusively', (individual.YES))
            individual.assign('immunizations_up_to_date', (individual.YES))
            individual.assign('current_medication_order', (individual.MEDIC_ORDER_ORS))
            individual.assign('mid_upper_arm_circumference', 90)
            individual.assign('oedema', (individual.YES))
            individual.assign('weight', 20)
            individual.assign('tests_ordered', individual.TEST_ORDER_MALARIA)
            individual.assign('referral_priority', individual.REFERRAL_URGENT)
            individual.assign('reasons_for_referral__regimen_failure', True)
            individual.assign('reasons_for_referral__convulsions', True)
            individual.assign('reasons_for_referral__abnormal_vaginal_bleeding', False)

            transmit_form(individual)
            message.respond("Individual form transmitted to OMRS.")
            household = OpenMRSHouseholdForm(create=False, mri=mri, location=1, \
                            provider=1, encounter_datetime=dt)

            household.assign('hh_member_available', household.NO)

            transmit_form(household)
            message.respond("Household form transmitted to OMRS.")

