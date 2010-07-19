#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _
from childcount.utils import clean_names
from childcount.forms import CCForm
from childcount.models import Patient, Encounter
from childcount.exceptions import ParseError, BadValue, Inapplicable


class UpdateNameForm(CCForm):
    KEYWORDS = {
        'en': ['uname'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT
    SURNAME_FIRST = False

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: | First Name | " \
                                "Last Name |"))
        #hold  previous Name
        pname = _(u" %(fname)s %(lname)s ") % {'fname': patient.first_name, \
                   'lname': patient.last_name}

        #set New Name
        patient.last_name, patient.first_name, alias = \
                             clean_names(' '.join(self.params[1:]), \
                             surname_first=self.SURNAME_FIRST)

        #fetch new name
        newname = _(u" %(fname)s %(lname)s ") % {'fname': \
                   patient.first_name, 'lname': patient.last_name}

        patient.save()

        #display response
        self.response = _("You successfuly changed name of %(patient)s to "  \
                          "%(newname)s") % {'patient': pname,  \
                            'newname': newname}
