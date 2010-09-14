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
    
    def hi(self):
        return u'jklop'

    @property
    def sleepingsite(self):
        try:
            z = BedNetReport.objects.get(encounter__patient=self).sleeping_sites
        except BedNetReport.DoesNotExist:
            z = 0
        return z

    @property
    def damagednets(self):
        try:
            z = BedNetReport.objects.get(encounter__patient=self).damaged_nets
        except BedNetReport.DoesNotExist:
            z = 0
        return z

    @property
    def functioningnets(self):
        try:
            z = BedNetReport.objects.get(encounter__patient=self).function_nets
        except BedNetReport.DoesNotExist:
            z = 0
        return z
        
    @property
    def earliernets(self):
        try:
            z = BedNetReport.objects.get(encounter__patient=self).earlier_nets
        except BedNetReport.DoesNotExist:
            z = 0
        return z

    @classmethod
    def return_household(cls):
        try:
            household = cls.objects.filter(health_id=F(\
                                                    'household__health_id'))
        except:
            pass

        else:
            return household

    @classmethod
    def summary(cls):
        columns = []
        columns.append(
            {'name': _("Household ".upper()),
            'bit': '{{object.household.health_id.upper}}'})
        columns.append(
            {'name': _("Household Name".upper()),
            'bit': 'XXXXX'})
        columns.append(
            {'name': _("No. Sleeping site".upper()),
             'bit': '{{object.sleepingsite}}'})
        columns.append(
            {'name': _("Functioning Bednet".upper()),
             'bit': '{{object.functioningnets}}'})
        columns.append(
            {'name': _("Earlier Bednets".upper()),
             'bit': '{{object.earliernets}}'})
        columns.append(
            {'name': _("Damaged Bednet".upper()),
             'bit': '{{object.damagednets}}'})
        columns.append(
            {'name': _("Primary Sanitation".upper()),
             'bit': '{{object.sleepingsite}}'})
        columns.append(
            {'name': _("Shared?".upper()),
             'bit': '{{object.sleepingsite}}'})
        columns.append(
            {'name': _("Primary source water".upper()),
             'bit': '{{object.sleepingsite}}'})
        columns.append(
            {'name': _("Treatment Method ".upper()),
             'bit': '{{object.sleepingsite}}'})

        sub_columns = None
        return columns, sub_columns

'''
class BdntClinicReport():

    class Meta:
        verbose_name = _("Community Health Worker Report")

    @classmethod
    def summary(cls):
        columns = []


        
        • Number of households that do not have any bednet coverage
        • Percentage of households that do not have any bednet coverage
        • Number of sleeping sites that have bednet coverage
        • Percentage of sleeping sites that have bednet coverage
        • Number of sleeping sites that do not have bednet coverage
        • Percentage of sleeping sites that do not have bednet coverage
        • How many bedn
       

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
        
'''
