#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from django.utils.translation import ugettext as _

from reporters.models import Reporter
from locations.models import Location

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated


class CheckHealthIdCommand(CCCommand):

    KEYWORDS = {
        'en': ['checkid', 'check'],
        'fr': ['checkid'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if self.params.__len__() < 2:
            self.message.respond(_(u"checkid command requires a health id"), \
                                   'error')
            return True
        health_id = self.params[1].upper()
        try:
            patient = Patient.objects.get(health_id__iexact=health_id)
            self.message.respond(_(u"%(patient)s; Household: %(household)s" % \
                                {'patient': patient, \
                                'household': patient.household}))
        except Patient.DoesNotExist:
            self.message.respond(_(u"No patient with health id %(health_id)s" \
                                    % {'health_id': health_id}), 'error')

        return True
