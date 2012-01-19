#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from django.utils.translation import ugettext as _

from checksum import checksum

from reporters.models import Reporter
from locations.models import Location
from childcount.models import HealthId

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated


class CheckHealthIdCommand(CCCommand):

    KEYWORDS = {
        'en': ['checkid', 'check'],
        'rw': ['checkid', 'check'],
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
            self.message.respond(_(u"SUCCESS: %(patient)s; Household: "
                                    "%(household)s; CHW: %(chw)s" % \
                                {'patient': patient, \
                                'household': patient.household,
                                'chw': patient.chw}), 'success')
            return True
        except Patient.DoesNotExist:
            pass

        try:
            health_id_obj = HealthId.objects.get(health_id__iexact=health_id)
        except HealthId.DoesNotExist:
            resp = _(u"Health ID %(id)s does NOT exist in the database ") \
                % {'id': health_id.upper()}
            if checksum.is_valid_identifier(health_id):
                resp += _(u" but IS a valid identifier.  Check to make sure "
                            "the database is current.")
            else:
                resp += _(u" and is NOT a valid identifier.  You might have "
                            "entered the ID incorrectly.")
            self.message.respond(resp, 'error')
            return True

        resp = _(u"Health ID %(id)s ") % {'id': health_id.upper()}
        if health_id_obj.status == HealthId.STATUS_GENERATED:
            resp += _(u" is valid but no patient has been registered "
                        "with this ID.")
        elif health_id_obj.status == HealthId.STATUS_PRINTED:
            resp += _(u" is valid but no patient has been registered "
                        "with this ID.")
        elif health_id_obj.status == HealthId.STATUS_ISSUED:
            resp += _(u" is marked as belonging to a patient, but that \
                        patient is unknown.")
        elif health_id_obj.status == HealthId.STATUS_REVOKED:
            resp += _(u" is in the database but is marked as UNUSABLE.",
                        'error')
        else:
            raise BadValue("Health ID is marked with an invalid status.",
                        'error')

        self.message.respond(resp)
        return True
