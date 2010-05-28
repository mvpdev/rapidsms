#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import Patient, Encounter
from childcount.models.reports import SPregnancy as SauriPregnancyReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class SauriPregnancyForm(CCForm):
    KEYWORDS = {
        'en': ['p'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    MIN_PREG_AGE = 9

    def process(self, patient):
        tested_hiv_field = MultipleChoiceField()
        tested_hiv_field.add_choice('en', \
                                SauriPregnancyReport.TESTED_YESREACTIVE, 'YR')
        tested_hiv_field.add_choice('en',
                                SauriPregnancyReport.TESTED_NOREACTIVE, 'NR')
        tested_hiv_field.add_choice('en', \
                                SauriPregnancyReport.TESTED_NOUNKNOWN, 'NU')
        tested_hiv_field.add_choice('en', \
                            SauriPregnancyReport.TESTED_YESNOTREACTIVE, 'YN')

        iron_supplement_field = MultipleChoiceField()
        iron_supplement_field.add_choice('en', \
                                        SauriPregnancyReport.IRON_YES, 'Y')
        iron_supplement_field.add_choice('en', \
                                        SauriPregnancyReport.IRON_NO, 'N')
        iron_supplement_field.add_choice('en', \
                                        SauriPregnancyReport.IRON_UNKNOWN, 'U')
        iron_supplement_field.add_choice('en', \
                                    SauriPregnancyReport.IRON_DOESNOTHAVE, 'X')

        folic_supplement_field = MultipleChoiceField()
        folic_supplement_field.add_choice('en', \
                                        SauriPregnancyReport.FOLIC_YES, 'Y')
        folic_supplement_field.add_choice('en', \
                                        SauriPregnancyReport.FOLIC_NO, 'N')
        folic_supplement_field.add_choice('en', \
                                    SauriPregnancyReport.FOLIC_UNKNOWN, 'U')
        folic_supplement_field.add_choice('en', \
                                SauriPregnancyReport.FOLIC_DOESNOTHAVE, 'X')

        cd4_count_field = MultipleChoiceField()
        cd4_count_field.add_choice('en', \
                                        SauriPregnancyReport.CD4_YES, 'Y')
        cd4_count_field.add_choice('en', \
                                        SauriPregnancyReport.CD4_NO, 'N')
        cd4_count_field.add_choice('en', \
                                        SauriPregnancyReport.CD4_UNKNOWN, 'U')

        if patient.gender != Patient.GENDER_FEMALE:
            raise Inapplicable(_(u"Only female patients can be pregnant"))

        if patient.years() < self.MIN_PREG_AGE:
            raise Inapplicable(_(u"Patient is too young to be pregnant " \
                                "(%(age)s)") % \
                                {'age': patient.humanised_age()})

        if len(self.params) < 7:
            raise ParseError(_(u"Not enough info, expected: " \
                                "| month of pregnancy | number of ANC " \
                                "visits | weeks since last ANC visit |"))

        try:
            pr = SauriPregnancyReport.objects.get(encounter=self.encounter)
            pr.reset()
        except SauriPregnancyReport.DoesNotExist:
            pr = SauriPregnancyReport(encounter=self.encounter)
        pr.form_group = self.form_group

        month = self.params[1]
        if not month.isdigit() or int(month) not in range(1, 10):
            raise BadValue(_("Month of pregnancy must be a number between "\
                               "1 and 9"))
        month = int(month)

        anc_visits = self.params[2]
        if not anc_visits.isdigit():
            raise ParseError(_('Number of ANC visits must be a number'))
        anc_visits = int(anc_visits)

        if anc_visits != 0 and len(self.params) < 4:
            raise ParseError(_(u"You must include the weeks since the last " \
                                "ANC visit after the total number of ANC "
                                "visits"))

        if anc_visits != 0:
            weeks = self.params[3]
            if not weeks.isdigit():
                raise ParseError(_(u"Weeks since last ANC visit must be a " \
                                    "number"))
            weeks = int(weeks)
        else:
            weeks = None

        tested_hiv_field.set_language(self.chw.language)
        iron_supplement_field.set_language(self.chw.language)
        folic_supplement_field.set_language(self.chw.language)
        cd4_count_field.set_language(self.chw.language)
        if not iron_supplement_field.is_valid_choice(self.params[4]):
            raise ParseError(_(u"Iron Supplement %(choices)s") % \
                            {'choices': \
                                iron_supplement_field.choices_string()})

        iron_supplement = iron_supplement_field.get_db_value(self.params[4])

        if not folic_supplement_field.is_valid_choice(self.params[5]):
            raise ParseError(_(u"Folic Acid Supplement %(choices)s") % \
                        {'choices': folic_supplement_field.choices_string()})

        folic_supplement = folic_supplement_field.get_db_value(self.params[5])

        if not tested_hiv_field.is_valid_choice(self.params[6]):
            raise ParseError(_(u"Tested HIV %(choices)s") % \
                            {'choices': tested_hiv_field.choices_string()})

        tested_hiv = tested_hiv_field.get_db_value(self.params[6])

        pr.tested_hiv = tested_hiv
        pr.iron_supplement = iron_supplement
        pr.folic_suppliment = folic_supplement

        if tested_hiv in (SauriPregnancyReport.TESTED_YESREACTIVE, \
                            SauriPregnancyReport.TESTED_NOREACTIVE):

            if len(self.params) < 9:
                raise ParseError(_(u"Not enough info, expected: " \
                                "please ask if CD4 count has been done and "\
                                "check if the patient is on pmtc arvs"))
            if not cd4_count_field.is_valid_choice(self.params[7]):
                raise ParseError(_(u"CD4 Count %(choices)s") % \
                                {'choices': cd4_count_field.choices_string()})

            cd4_count = cd4_count_field.get_db_value(self.params[7])

            pmtc_arv = self.params[8]
            #TODO check against Coded items

            pr.cd4_count = cd4_count
            pr.pmtc_arv = pmtc_arv

        #TODO Cases
        '''
        pcases = Case.objects.filter(patient=patient, \
                                     type=Case.TYPE_PREGNANCY, \
                                     status=Case.STATUS_OPEN)

        if pcases.count() == 0:
            #create a new pregnancy case
            now = datetime.now()
            #expected birth date
            expires_on = now - timedelta(int((9 - month) * 30.4375))
            case = Case(patient=patient, type=Case.TYPE_PREGNANCY, \
                 expires_on=expires_on)
            case.save()
        else:
            case = pcases.latest()
        #TODO give this feedback
        if month == 2 and clinic_visits < 1 \
            or month == 5 and clinic_visits < 2 \
            or month == 7 and clinic_visits < 3 \
            or month == 8 and clinic_visits < 8:
            response += _('Remind the woman she is due for a clinic visit')
        '''

        pr.pregnancy_month = month
        pr.anc_visits = anc_visits
        pr.weeks_since_anc = weeks

        pr.save()

        if weeks == 0:
            last_str = _(u" less than one week ago")
        elif weeks == 1:
            last_str = _(u" one week ago")
        elif weeks > 1:
            last_str = _(u" %(weeks)d weeks ago") % {'weeks': weeks}

        self.response = _(u"%(month)d months pregnant with %(visits)d ANC " \
                           "visits") % {'month': month, \
                                        'visits': anc_visits}
        if weeks is not None:
            self.response += _(u", last ANC visit %s") % last_str
