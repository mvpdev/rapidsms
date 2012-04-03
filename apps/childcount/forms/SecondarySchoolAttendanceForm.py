#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import SchoolAttendanceReport
from childcount.models import CodedItem
from childcount.exceptions import ParseError, BadValue


class SecondarySchoolAttendanceForm(CCForm):
    """ SecondarySchoolAttendanceForm

    Params:
        * SecondarySchoolAttendanceForm
    """

    KEYWORDS = {
        'en': ['ss'],
        'rw': ['ss'],
        'fr': ['ss'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected:  " \
                                " | number of secondary school aged pupils" \
                                " in the household" \
                                " | number attending secondary school "))

        try:
            psa = SchoolAttendanceReport.objects.get(encounter=self.encounter)
        except SchoolAttendanceReport.DoesNotExist:
            psa = SchoolAttendanceReport(encounter=self.encounter)
        psa.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of secondary school aged pupils in" \
                                " the household must be entered as a number."))

        psa.household_pupil = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of secondary school aged pupils  " \
                                "atttending secondary school must be" \
                                " entered as a number."))
        psa.attending_school = int(self.params[2])

        if psa.attending_school > psa.household_pupil:
            raise BadValue(_(u"The number of school aged pupils atttending  " \
                               "secondary school cannot be greater than the " \
                               "total number of secondary school aged pupils" \
                               " in the household "))

        psa.save()
        self.response = _(u"%(pupil)d school aged Pupil, %(attend)d " \
                               "attending school ") % \
                               {'pupil': psa.household_pupil, \
                               'attend': psa.attending_school}
