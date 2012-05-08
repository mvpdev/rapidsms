#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import SchoolAttendanceReport
from childcount.models import CodedItem
from childcount.exceptions import ParseError, BadValue


class PrimarySchoolAttendanceForm(CCForm):
    """ PrimarySchoolAttendanceForm

    Params:
        * PrimarySchoolAttendanceForm
    """

    KEYWORDS = {
        'en': ['sa'],
        'rw': ['sa'],
        'fr': ['sa'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected:  " \
                                " | number of primary school aged pupils in " \
                                "the household | number attending primary " \
                                "school "))

        try:
            psa = SchoolAttendanceReport.objects.get(encounter=self.encounter)
        except SchoolAttendanceReport.DoesNotExist:
            psa = SchoolAttendanceReport(encounter=self.encounter)
        psa.form_group = self.form_group
        sa1 = self.params[1]
        if not sa1.isdigit() and sa1.upper() != 'N':
            raise ParseError(_(u"| Number of primary school aged pupils in " \
                                "the household must be entered as a number." \
                                " OR 'N' for school not in session"))
        else:
            psa.household_pupil = -1
            psa.save()
            self.response = _("School NOT in Session.")
            return True
        psa.household_pupil = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"| Number of primary school aged pupils  " \
                                "atttending primary school must be entered " \
                                "as a number."))
        psa.attending_school = int(self.params[2])

        if psa.attending_school > psa.household_pupil:
            raise BadValue(_(u"The number of school aged pupils atttending  " \
                               "primary school cannot be greater than the " \
                               "total number of primary school aged pupils " \
                               "in the household "))

        psa.save()
        self.response = _(u"%(pupil)d school aged Pupil, %(attend)d " \
                           "attending school ") % \
                               {'pupil': psa.household_pupil, \
                               'attend': psa.attending_school}
