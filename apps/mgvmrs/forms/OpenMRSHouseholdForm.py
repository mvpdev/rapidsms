#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from mgvmrs.forms.OpenMRSFormInterface import *


class OpenMRSHouseholdForm(OpenMRSFormInterface):

    template_name = 'OpenMRSHouseholdForm.xml'

    # concepts
    YES = '1065^YES^99DCT'
    NO = '1066^NO^99DCT'

    # Allowed answers
    # (TYPE, LIST OF VALUES)
    fields = {
        'hh_member_available': (OpenMRSFormInterface.T_CWE, (YES, NO)),
        'number_children_under_five': (OpenMRSFormInterface.T_NM, None),
        'counseling_topics__nutrition': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'counseling_topics__bednet': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'counseling_topics__family_planning': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'counseling_topics__sanitation_and_hygiene': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'counseling_topics__alcohol': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'counseling_topics__tobacco': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'counseling_topics__other_non_coded': \
                                           (OpenMRSFormInterface.T_BOOL, None),
        'other_sick_members': (OpenMRSFormInterface.T_NM, None),
        'rdts_used': (OpenMRSFormInterface.T_NM, None),
        'positive_rdts': (OpenMRSFormInterface.T_NM, None),
        'other_sick_members_on_treatment': (OpenMRSFormInterface.T_NM, None),
        'women_seen': (OpenMRSFormInterface.T_NM, None),
        'women_using_family_planning': (OpenMRSFormInterface.T_NM, None),
        'sleeping_sites': (OpenMRSFormInterface.T_NM, None),
        'bednets': (OpenMRSFormInterface.T_NM, None),
    }


    values = {}
