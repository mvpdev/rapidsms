#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import DangerSignsReport
from childcount.models import CodedItem
from childcount.exceptions import ParseError


class DangerSignsForm(CCForm):
    KEYWORDS = {
        'en': ['s'],
        'fr': ['s'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: danger sign " \
                                "codes"))

        try:
            dsr = DangerSignsReport.objects.get(encounter=self.encounter)
        except DangerSignsReport.DoesNotExist:
            dsr = DangerSignsReport(encounter=self.encounter)
        dsr.form_group = self.form_group

        danger_signs = dict([(danger_sign.local_code.lower(), danger_sign) \
                             for danger_sign in \
                             CodedItem.objects.filter(\
                                type=CodedItem.TYPE_DANGER_SIGN)])
        valid = []
        unkown = []
        for d in self.params[1:]:
            obj = danger_signs.get(d, None)
            if obj is not None:
                valid.append(obj)
            else:
                unkown.append(d)

        if unkown:
            invalid_str = _(u"Unkown danger sign code(s): %(codes)s " \
                             "No danger signs recorded.") % \
                             {'codes': ', '.join(unkown).upper()}
            raise ParseError(invalid_str)

        if valid:
            signs_string = ', '.join([ds.description for ds in valid])
            self.response = _(u"Danger signs: %(ds)s") % {'ds': signs_string}
            dsr.save()
            for obj in valid:
                dsr.danger_signs.add(obj)
            dsr.save()
