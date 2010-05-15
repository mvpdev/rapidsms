#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from mgvmrs.forms.OpenMRSFormInterface import *


class OpenMRSConsultationForm(OpenMRSFormInterface):

    ''' Consultation Form

    Matches OpenMRS Form #9 '''

    template_name = 'OpenMRSConsultationForm.xml'

    # concepts
    YES = '1065^YES^99DCT'
    NO = '1066^NO^99DCT'
    UNKNOWN = '1067^UNKNOWN^99DCT'

    UNAVAILABLE = '1899^Patient currently unavailable^99DCT'
    INPATIENT = '1896^PATIENT CURRENTLY INPATIENT AT FACILITY^99DCT'

    TEST_ORDER_MALARIA = '1643^RAPID TEST FOR MALARIA^99DCT'
    TEST_ORDER_NONE = '1107^NONE^99DCT'

    POSITIVE = '703^POSITIVE^99DCT'
    NEGATIVE = '664^NEGATIVE^99DCT'
    INDETERMINATE = '1138^INDETERMINATE^99DCT'

    MEDIC_ORDER_ANTIMALARIAL = '5839^ANTIMALARIAL MEDICATIONS^99DCT'
    MEDIC_ORDER_ZINC = '86672^Zinc^99DCT'
    MEDIC_ORDER_ORS = '351^ORAL REHYDRATION SALTS^99DCT'

    REFERRAL_AMBULANCE = '1905^Emergency-Ambulance Required (Status)^99DCT'
    REFERRAL_EMERGENCY = '1882^Emergency (status)^99DCT'
    REFERRAL_URGENT = '1883^Urgent (status)^99DCT'
    REFERRAL_WHEN_CONVENIENT = '1884^When Convenient status)^99DCT'

    REASON_NT = 'regimen_failure'
    REASON_AS = 'physical_trauma'
    REASON_BM = 'no_fetal_movements'
    REASON_BV = 'blurred_vision'
    REASON_CC = 'cough'
    REASON_CV = 'convulsions'
    REASON_CW = 'cough_lasting_more_than_3_weeks'
    REASON_FP = 'fever_in_first_trimester_of_pregnancy'
    REASON_NB = 'night_blindness'
    REASON_OD = 'oedema'
    REASON_PA = 'abdominal_pain'
    REASON_PD = 'postpartum_depression'
    REASON_PH = 'severe_headache'
    REASON_PU = 'dysuria'
    REASON_SP = 'dermatitis'
    REASON_SW = 'peripheral_edema'
    REASON_VB = 'abnormal_vaginal_bleeding'
    REASON_VD = 'vaginal_discharge'
    REASON_VP = 'acute_vaginitis'
    REASON_WL = 'weight_loss'
    REASON_ND = 'unable_to_drink'
    REASON_Z = 'other_non-coded'

    # answers group
    A_YESNO = (YES, NO, UNKNOWN)
    A_POSIT = (POSITIVE, NEGATIVE, INDETERMINATE)

    # Allowed answers
    # (TYPE, LIST OF VALUES)
    fields = {
        'patients_condition_improved': (OpenMRSFormInterface.T_CWE, \
                                        (YES, NO, UNKNOWN, UNAVAILABLE)),
        'visit_to_health_facility_since_last_home_visit': \
                                         (OpenMRSFormInterface.T_CWE, \
                                          (YES, NO, UNKNOWN, INPATIENT)),
        'danger_signs_present': (OpenMRSFormInterface.T_CWE, A_YESNO),
        'month_of_current_gestation': (OpenMRSFormInterface.T_NM, None),
        'antenatal_visit_number': (OpenMRSFormInterface.T_NM, None),
        'weeks_since_last_anc': (OpenMRSFormInterface.T_NM, None),

        'number_of_health_facility_visits_since_birth': \
                                             (OpenMRSFormInterface.T_NM, None),
        'breastfed_exclusively': (OpenMRSFormInterface.T_CWE, A_YESNO),
        'immunizations_up_to_date': (OpenMRSFormInterface.T_CWE, A_YESNO),
        'mid_upper_arm_circumference': (OpenMRSFormInterface.T_NM, None),
        'oedema': (OpenMRSFormInterface.T_CWE, A_YESNO),
        'weight': (OpenMRSFormInterface.T_NM, None),
        'tests_ordered': (OpenMRSFormInterface.T_CWE, \
                          (TEST_ORDER_MALARIA, TEST_ORDER_NONE)),
        'rapid_test_for_malaria': (OpenMRSFormInterface.T_CWE, A_POSIT),
        'current_medication_order': (OpenMRSFormInterface.T_ZZ, \
                                     (MEDIC_ORDER_ANTIMALARIAL, \
                                      MEDIC_ORDER_ORS, \
                                      MEDIC_ORDER_ZINC)),
        'referral_priority': (OpenMRSFormInterface.T_CWE, \
                                     (REFERRAL_AMBULANCE, \
                                      REFERRAL_EMERGENCY, \
                                      REFERRAL_URGENT, \
                                      REFERRAL_WHEN_CONVENIENT)),
        'reasons_for_referral__regimen_failure': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__physical_trauma': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__no_fetal_movements': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__blurred_vision': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__cough': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__convulsions': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__cough_lasting_more_than_3_weeks': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__fever_in_first_trimester_of_pregnancy': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__night_blindness': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__oedema': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__abdominal_pain': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__postpartum_depression': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__severe_headache': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__dysuria': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__dermatitis': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__peripheral_edema': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__abnormal_vaginal_bleeding': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__vaginal_discharge': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__acute_vaginitis': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__weight_loss': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__unable_to_drink': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'reasons_for_referral__other_non_coded': \
                                           (OpenMRSFormInterface.T_BOOL, None),
    }


    values = {}
