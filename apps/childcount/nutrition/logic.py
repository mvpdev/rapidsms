#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Nutrition Logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Patient import Patient
from childcount.core.models.Case import Case
from childcount.core.models.Referral import Referral
from childcount.nutrition.models import MUACReport

def muac_section(created_by, health_id, muac, oedema):
    '''1.4) Nutrition (MUAC) Section (6-59 months)'''
    patient = Patient.objects.get(health_id=health_id)
    days, months = patient.age_in_days_months()
    response = ''

    if days <= 30:
        response =  _('Child is too young for MUAC')
    elif months > 59:
        response = _('Child is older then 59 months. For any concerns about '\
                     'child in the future please go to the clinic. (Please '\
                     'advise mother to still closely monitor child and refer '\
                     'them to the clinic any time there is a concern). '\
                     'Positive reinforcement')
    else:
        if muac < 50:
            response = _('MUAC is too low. Please verify if correct and '\
                         'resend report. If correct please refer child '\
                         'IMMEDIATELY!')
        elif muac > 250:
            response = _('MUAC is too high. Please verify it is correct '\
                         'and resend report.')
        else:
            if oedema.upper() in ('Y', 'O', 'E'):
                oedema = 'Y'
            else:
                oedema = 'N'
            mr = MUACReport(created_by=created_by, oedema=oedema, muac=muac, \
                            patient=patient)
            mr.save()
            if mr.status == MUACReport.STATUS_SEVERE:
                info = {}
                info.update({'last_name': patient.last_name,
                             'first_name': patient.first_name,
                             'age': patient.age(),
                             'zone': patient.zone})
                rf = Referral(patient=patient)
                info.update({'refid': rf.referral_id})

                expires_on = datetime.now() + timedelta(15)
                case = Case(patient=patient, expires_on=expires_on)
                case.save()

                response = _('SAM> Last, First (AGE) LOCATION has acute '\
                         'malnutrition. Please refer child to clinic '\
                         'IMMEDIATELY. (%(refid)s')
                #setup alert
                # SAM> Last, First (AGE), LOCATION has SAM. CHW NAME - 
                #CHWMOBILE. (REFID)
            else:
                response = _('MUAC %(muac)s(mm), Oedema=%(oedema)s.') % \
                    {'muac': mr.muac, 'oedema': mr.oedema} 

    return response
