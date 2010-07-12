#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import gettext as _
from django.db.models import F

from datetime import date, timedelta, datetime

from childcount.models import Patient
from locations.models import Location
from childcount.models import CHW
from childcount.models import BedNetReport, BednetUtilization, \
                                        BednetIssuedReport
from logger.models import IncomingMessage


class BednetHousehold(Patient):

    class Meta:
        verbose_name = _("Household Report")
        proxy = True

    @property
    def active_sleepingsite(self):
        try:
            sleeping_site = BedNetReport.objects.get(encounter__patient \
                                     =self.encounter.patient)
        except BedNetReport.DoesNotExist:
            sleeping_site = 0
        return sleeping_site

    @property
    def functioning_bednet(self):
        try:
            functioning_bednet = BedNetReport.objects.get(encounter__patient \
                                     =self.encounter.patient).nets
        except BedNetReport.DoesNotExist:
            functioning_bednet = 0
        return 2

    @classmethod
    def return_household(cls):
        try:
            household = Patient.objects.filter(health_id=F(\
                                                    'household__health_id'))
        except: 
            pass

        else:
            return household

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': _("Household ".upper()), \
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': _("Household Name".upper()), \
            'bit': '{{object.last_name}} {{object.first_name}}'})
        columns.append(
            {'name': "No. Sleeping site".upper(), \
             'bit': '{{active_sleepingsite.sleeping_sites}}'})
        columns.append(
            {'name': "Functioning Bednet".upper(), \
             'bit': '{{object.functioning_bednet}}'})
        columns.append(
            {'name': "Bed Net needed".upper(), \
             'bit': '2'})
        columns.append(
            {'name': "ChW".upper(), \
             'bit': '{{object.chw}}'})

        sub_columns = None
        return columns, sub_columns



class BdntClinicReport():

    class Meta:
        verbose_name = _("Community Health Worker Report")

    @classmethod
    def summary(cls):
        columns = []


        '''
        • Number of households that do not have any bednet coverage
        • Percentage of households that do not have any bednet coverage
        • Number of sleeping sites that have bednet coverage
        • Percentage of sleeping sites that have bednet coverage
        • Number of sleeping sites that do not have bednet coverage
        • Percentage of sleeping sites that do not have bednet coverage
        • How many bedn
        '''

        columns.append(
            {'name': _(u"Number of household tied to clinic".upper()), \
             'bit': '@{{ object.alias }}'})
        columns.append(
            {'name': _("Full Bednet coverage".upper()), \
             'bit': '{{ object.first_name }} {{ object.last_name }}'})
        columns.append(
            {'name':  _("% Full Bednet coverage".upper()),\
             'bit': ''})
        columns.append(
            {'name': "% Partial Bednet coverage".upper(), \
             'bit': ''})
        columns.append(
            {'name': "% Partial Bednet coverage".upper(), \
             'bit': ''})
        columns.append(
            {'name': " Partial/full Bednet coverage".upper(), \
             'bit': ''})
        columns.append(
            {'name': "% Partial/full Bednet coverage".upper(), \
             'bit': ''})


        sub_columns = None
        return columns, sub_columns

