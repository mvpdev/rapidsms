#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from mgvmrs.forms.OpenMRSFormInterface import *


class OpenMRSLabRequestForm(OpenMRSFormInterface):

    '''
    Lab Request Form
    '''

    template_name = 'OpenMRSLabRequestForm.xml'

    # concepts

    # Allowed answers
    # (TYPE, LIST OF VALUES)
    fields = {
        'test_sputum_for_acid_fast_bacilli': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'test_whitecell':                 (OpenMRSFormInterface.T_BOOL, None),
        'test_platelets':                 (OpenMRSFormInterface.T_BOOL, None),
        'test_erythrocyte':               (OpenMRSFormInterface.T_BOOL, None),
        'test_serum_glucose_rb':          (OpenMRSFormInterface.T_BOOL, None),
        'test_serum_fasting_fb':          (OpenMRSFormInterface.T_BOOL, None),
        'test_widaltest':                 (OpenMRSFormInterface.T_BOOL, None),
        'test_G6PD':                      (OpenMRSFormInterface.T_BOOL, None),
        'test_malaria_smear_qualitative': (OpenMRSFormInterface.T_BOOL, None),
        'test_cd4':             (OpenMRSFormInterface.T_BOOL, None),
        'test_hemoglobin':      (OpenMRSFormInterface.T_BOOL, None),
        'test_hepatitisb':      (OpenMRSFormInterface.T_BOOL, None),
        'test_vdrl':            (OpenMRSFormInterface.T_BOOL, None),
        'test_rhesus':          (OpenMRSFormInterface.T_BOOL, None),
        'test_sickle_cell':     (OpenMRSFormInterface.T_BOOL, None),
        'test_bloodgroup':      (OpenMRSFormInterface.T_BOOL, None),
    }

    values = {}
