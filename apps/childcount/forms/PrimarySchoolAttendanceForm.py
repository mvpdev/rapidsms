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
        'en': ['sp'],
        'rw': ['sp'],
        'fr': ['sp'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 4:
            raise ParseError(_(u"Not enough info. Expected:  " \
                                " | number of primary school aged pupils in " \
                                "the household" \
                                " | number of primary school aged pupils  " \
                                "atttending school" \
                                " | number of under/over pupils atttending " \
                                " primary school" \
                                " | reason for not attending school |"))

        try:
            psa = SchoolAttendanceReport.objects.get(encounter=self.encounter)
        except SchoolAttendanceReport.DoesNotExist:
            psa = SchoolAttendanceReport(encounter=self.encounter)
        psa.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"| Number of primary school aged pupils in " \
                                "the household must be entered as a number."))

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

        if not self.params[3].isdigit():
            raise ParseError(_(u"| Number of under/over school aged pupils  " \
                                "atttending primary school must be entered " \
                                " as a number."))

        psa.attendschool_other = int(self.params[3])
        psa.school_type = psa.PRIMARY_SCHOOL

        if psa.household_pupil - psa.attending_school == 0:
            self.response = _(u"%(pupil)d school aged Pupil, %(attend)d " \
                               "attending school, %(over_attend)d under/over  " \
                               "age attending school") % \
                               {'pupil': psa.household_pupil, \
                               'attend': psa.attending_school, \
                               'over_attend': psa.attendschool_other }
            psa.save()
            return

        if len(self.params) < 5:
            raise ParseError(_(u"After entering number of under/over school  " \
                                "aged pupils attending primary school, you  " \
                                "must state reason for those not attending"))
                                
        num = psa.household_pupil - psa.attending_school
        if len(self.params[4:]) < num:
            raise ParseError(_(u"You must specify %(num)d reason for not   " \
                                "attending school code(s). One for each of " \
                                "the %(num)s pupil not attending school") % \
                                {'num': num})

        reasons = dict([(reason.local_code.lower(), reason) \
                             for reason in \
                             CodedItem.objects.filter(\
                                type=CodedItem.TYPE_SCHOOLREASON)])
        valid = []
        unkown = []
        for d in self.params[4:]:
            obj = reasons.get(d, None)
            if obj is not None:
                valid.append(obj)
            else:
                unkown.append(d)

        if unkown:
            invalid_str = _(u"Unkown Reason for not attending school " \
                              "code(s): %(codes)s " \
                          "No Primary school attendance recorded.") % \
                         {'codes': ', '.join(unkown).upper()}
            raise ParseError(invalid_str)

        if valid:
            psa.save()
            for obj in valid:
                psa.reason.add(obj)
            psa.save()
            reason_string = ', '.join([r.description for r in valid])
            self.response = _(u"%(pupil)d school aged Pupil, %(attend)d " \
                               "attending school, %(over_attend)d under/over  " \
                               "age attending school: %(r_string)s") % \
                               {'pupil': psa.household_pupil, \
                               'attend': psa.attending_school, \
                                'r_string': reason_string, \
                               'over_attend': psa.attendschool_other }
