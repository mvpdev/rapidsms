#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated
from childcount.exceptions import ParseError, BadValue

class FamilyCommand(CCCommand):

    KEYWORDS = {
        'en': ['family', 'fam'],
        'rw': ['family', 'fam'],
        'fr': ['famille', 'fam'],
    }

    @authenticated
    def process(self):
        if len(self.params) != 2:
            raise BadValue(_("Usage: %(com)s health_id") % \
                {'com': self.params[0]})

        try:
            patient = Patient.objects.get(health_id = self.params[1])
        except Patient.DoesNotExist:
            raise BadValue(_("No patient with health id %(hid)s") \
                % {'hid': self.params[1].upper()})

        household = Patient\
            .objects\
            .filter(household__health_id=patient.household.health_id)\
            .order_by('dob')

        out_str = _("Family of %(hid)s: ") % \
            {'hid': patient.health_id.upper()}
        out_str += ''.join(["(%(hh)s%(dead)s%(inact)s%(hid)s: %(name)s/%(gen)s/%(age)s) " \
            % {'hid': p.health_id.upper(),
                'hh': '[HH]' if p.is_head_of_household() else '',
                'dead': '[D]' if (p.status==Patient.STATUS_DEAD) else '',
                'inact': '[I]' if (p.status==Patient.STATUS_INACTIVE) else '',
                'name': p.full_name(),
                'gen': p.gender.upper(),
                'age': p.humanised_age()} \
            for p in household])

        self.message.respond(out_str, 'success')
        return True
