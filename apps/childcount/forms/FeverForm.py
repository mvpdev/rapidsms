#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

'''Fever Logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group

from childcount.forms.CCForm import CCForm
from childcount.forms.DangerSignsForm import DangerSignsForm
from childcount.forms.ReferralForm import ReferralForm
from childcount.forms.MedicineGivenForm import MedicineGivenForm
from childcount.models import Encounter
from childcount.models import CodedItem
from childcount.models.reports import FeverReport
from childcount.models.reports import DangerSignsReport
from childcount.models.reports import ReferralReport
from childcount.models.reports import MedicineGivenReport
from childcount.forms.utils import MultipleChoiceField
from childcount.utils import send_msg
from childcount.exceptions import ParseError, Inapplicable


class FeverForm(CCForm):
    """Fever

    Params:
        * rdt result (Y/N/U)
    """

    KEYWORDS = {
        'en': ['f'],
        'rw': ['f'],
        'fr': ['f'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT
    _short_msg = ''
    _fever_report = ''

    def process(self, patient):
        rdt_field = MultipleChoiceField()
        rdt_field.add_choice('en', FeverReport.RDT_POSITIVE, 'Y')
        rdt_field.add_choice('en', FeverReport.RDT_NEGATIVE, 'N')
        rdt_field.add_choice('en', FeverReport.RDT_UNKNOWN, 'U')
        rdt_field.add_choice('rw', FeverReport.RDT_POSITIVE, 'Y')
        rdt_field.add_choice('rw', FeverReport.RDT_NEGATIVE, 'N')
        rdt_field.add_choice('rw', FeverReport.RDT_UNKNOWN, 'U')
        rdt_field.add_choice('fr', FeverReport.RDT_POSITIVE, 'O')
        rdt_field.add_choice('fr', FeverReport.RDT_NEGATIVE, 'N')
        rdt_field.add_choice('fr', FeverReport.RDT_UNKNOWN, 'I')

        try:
            fr = FeverReport.objects.get(encounter=self.encounter)
            fr.reset()
        except FeverReport.DoesNotExist:
            fr = FeverReport(encounter=self.encounter)
        fr.form_group = self.form_group

        rdt_field.set_language(self.chw.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: %s") % \
                                                rdt_field.choices_string)

        if not rdt_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"RDT Result must be %(choices)s.") % \
                              {'choices': rdt_field.choices_string()})

        days, weeks, months = patient.age_in_days_weeks_months(\
            self.encounter.encounter_date.date())

        rdt = rdt_field.get_db_value(self.params[1])
        if rdt == FeverReport.RDT_POSITIVE:
            years = patient.years()
            tabs, yage = None, None
            # just reformatted to make it look like less ugh
            if years < 1:
                if months < 2:
                    tabs, yage = None, None
                else:
                    tabs, yage = 1, _("less than 3")
            elif years < 3:
                tabs, yage = 1, _("less than 3")
            elif years < 9:
                tabs, yage = 2, years
            elif years < 15:
                tabs, yage = 3, years
            else:
                tabs, yage = 4, years
            # no tabs means too young
            if not tabs:
                instructions = (_(u"Child is too young for treatment." \
                    " Please refer IMMEDIATELY to clinic."))
            else:
                instructions = _(u"Child is %(age)s. Please provide "\
                                  "%(tabs)s tab%(plural)s of Coartem "\
                                  "(ACT) twice a day for 3 days.") % \
                                   {'age': yage, \
                                    'tabs': tabs, \
                                    'plural': (tabs > 1) and 's' or ''}
            self._short_msg = _("Positive RDT result. ")
            self.response = self._short_msg + instructions

            '''alert = \
                _("MRDT> Child %(last_name)s, %(first_name)s, "\
                "%(gender)s/%(age)s (%(zone)s) has MALARIA%(danger)s. "\
                      "CHW: ..." % info)

            expires_on = datetime.now() + timedelta(7)
            case = Case(patient=patient, expires_on=expires_on, \
                        type=Case.TYPE_FEVER)
            case.save()
            '''
        elif rdt == FeverReport.RDT_NEGATIVE:
            self.response = _(u"Negative RDT result.")
            self._short_msg = self.response
        elif rdt == FeverReport.RDT_UNKNOWN:
            self.response = _(u"Unknown RDT result.")
            self._short_msg = self.response

        fr.rdt_result = rdt
        fr.save()
        self._fever_report = fr

    def post_process(self, forms_list):
        danger_signs = ""
        referred_str = ""
        meds = ""
        for form in forms_list:
            # get the form object/class 
            k = form['obj']
            if isinstance(k, DangerSignsForm):
                dsr = DangerSignsReport.objects.get(encounter=k.encounter)
                fv = CodedItem.by_local_code(CodedItem.TYPE_DANGER_SIGN, 'fv')
                only_fever = fv in dsr.danger_signs.all()
                if dsr.danger_signs.all().count() == 1 and only_fever:
                   pass
                else:
                    tmp = [ds.description for ds in dsr.danger_signs.all()]
                    danger_signs = u", " . join(tmp)
            if isinstance(k, ReferralForm):
                rfr = ReferralReport.objects.get(encounter=k.encounter)
                referred_str = rfr.get_urgency_display()
            if isinstance(k, MedicineGivenForm):
                mgr = MedicineGivenReport.objects.get(encounter=k.encounter)
                medicines = mgr.medicines.all()
                meds = _(u" Given: ")
                meds += u", " . join([med.description for med in medicines])
                meds += "."
                
        if danger_signs != "":
            msg = _(u"%(patient)s has %(msg)s %(danger_signs)s.%(meds)s "
                    "%(referral)s %(chw)s %(mobile)s." % {'patient':
                                    self._fever_report.encounter.patient,
                                    'msg': self._short_msg,
                                    'danger_signs': danger_signs,
                                    'referral': referred_str,
                                    'meds': meds,
                                    'chw' : self.chw,
                                    'mobile': self.chw.connection().identity})
            #alert facilitators
            try:
                g = Group.objects.get(name='Facilitator')
                for user in g.user_set.all():
                    send_msg(user.reporter, msg)
            except Group.DoesNotExist:
                pass
