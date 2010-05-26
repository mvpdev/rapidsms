#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from sref_generic_states import Sref


class MicroscopyResult(Sref):
    """
    Specimen sample state to be used when a specimen has been
    tested with microscopy.
    """

    state_name = 'microscopy'

    class Meta:
        app_label = 'findtb'


    def get_web_form(self):
        pass


    def get_short_message(self):
       return u"Received at NTRL"


    def get_long_message(self):
        return u"Received specimen TC#%(tc_number)s, patient %(patient)s " \
                "from %(dtu)s" % \
               {'dtu': self.specimen.location, \
                'patient': self.specimen.patient, \
                'tc_number': self.specimen.tc_number}
