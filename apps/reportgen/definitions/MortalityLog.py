#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

import time
from datetime import date

from django.db.models import F
from django.utils.translation import ugettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section, Paragraph

from locations.models import Location
from childcount.models import CHW, DeadPerson
from childcount.models.reports import DeathReport, StillbirthMiscarriageReport

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

_variants = [('All Locations', 'all', {'loc_pk': 0})]
_chw_locations = CHW.objects.values('location').distinct()
_locations = [(loc.name, loc.code, {'loc_pk': loc.pk}) \
                            for loc in Location.objects\
                                                .filter(pk__in=_chw_locations)]
_variants.extend(_locations)


class ReportDefinition(PrintedReport):
    """ list all Patients """
    title = 'Mortality Log'
    filename = 'mortality_log'
    formats = ['html', 'pdf', 'xls']
    variants = _variants

    def generate(self, time_period, rformat, title, filepath, data):
        doc = Document(title)
        
        self.current = 0
        self.data = data
        self.set_progress(0)
        
        #Death with Health ID
        table = self._create_table()
        self._add_dda_data(table)
        self._add_ddb_data(table)
        self._add_still_data(table)
        doc.add_element(table)
                        
        #current += 1
        #self.set_progress(100.0*current/total)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

    def _create_table(self):
        table = Table(12)
        table.add_header_row([
            Text(_(u'HID')),
            Text(_(u'Location Code')),
            Text(_(u'First Name.')),
            Text(_(u'Family Name.')),
            Text(_(u'Gen.')),
            Text(_(u'DOB.')),
            Text(_(u'AGE(Y/M).')),
            Text(_(u'HOH.')),
            Text(_(u'DOD')),
            Text(_(u'-----')),
            Text(_(u'Encounter Date')),
            Text(_(u'CHW'))])

        return table

    def _add_dda_data(self, table):
        """ DEATH WITH HEALTH ID """
        if 'loc_pk' not in self.data or self.data['loc_pk'] == 0:
            plist = DeathReport.objects.all()\
                .order_by('encounter__patient__location', 'encounter__chw',
                          'encounter__encounter_date')
        else:
            loc_pk = self.data['loc_pk']
            plist = DeathReport.objects\
                .filter(encounter__patient__location__pk=loc_pk)\
                .order_by('encounter__patient__location', 'encounter__chw',
                          'encounter__encounter_date')

        for row in plist:
            table.add_row([
                    Text(unicode(row.encounter.patient.health_id)),
                    Text(unicode(row.encounter.patient.location.code.upper())),
                    Text(unicode(row.encounter.patient.first_name)),
                    Text(unicode(row.encounter.patient.last_name)),
                    Text(unicode(row.encounter.patient.gender)),
                    Text(unicode(row.encounter.patient.dob)),
                    Text(unicode(row.encounter.patient.humanised_age())),
                    Text(unicode(row.encounter.patient.household.health_id)),
                    Text(unicode(row.death_date)),
                    Text(u"---"),
                    Text(unicode(row.encounter.encounter_date)),
                    Text(unicode(row.encounter.patient.chw))])

    def _add_ddb_data(self, table):
        """ DEATH WITHOUT HEALTH ID """
        if 'loc_pk' not in self.data or self.data['loc_pk'] == 0:
            plist = DeadPerson.objects.all()\
                .order_by('location', 'chw')
        else:
            loc_pk = self.data['loc_pk']
            plist = DeadPerson.objects.filter(chw__location__pk=loc_pk)\
                .order_by('location', 'chw')
        
        for row in plist:
            try:
                hoh = row.household.health_id.upper()
            except:
                hoh = u"---"
            table.add_row([
                    Text(u"---"),
                    Text(unicode(row.chw.location.code.upper())),
                    Text(unicode(row.first_name)),
                    Text(unicode(row.last_name)),
                    Text(unicode(row.gender)),
                    Text(unicode(row.dob)),
                    Text(unicode(row.humanised_age())),
                    Text(unicode(hoh)),
                    Text(unicode(row.dod)),
                    Text(u"---"),
                    Text(unicode(row.created_on)),
                    Text(unicode(row.chw))])

    def _add_still_data(self, table):
        """ STILL BIRTH AND MISCARIAGE"""
        if 'loc_pk' not in self.data or self.data['loc_pk'] == 0:
            plist = StillbirthMiscarriageReport.objects.all()\
                .order_by('encounter__patient__location', 'encounter__chw',
                          'encounter__encounter_date')
        else:
            loc_pk = self.data['loc_pk']
            plist = StillbirthMiscarriageReport.objects\
                .filter(encounter__patient__location__pk=loc_pk)\
                .order_by('encounter__patient__location', 'encounter__chw',
                          'encounter__encounter_date')

        for row in plist:
            table.add_row([
                    Text(unicode(row.encounter.patient.health_id)),
                    Text(unicode(row.encounter.patient.location.code.upper())),
                    Text(u"---"),
                    Text(u"---"),
                    Text(u"---"),
                    Text(u"---"),
                    Text(u"---"),
                    Text(unicode(row.encounter.patient.household.health_id)),
                    Text(unicode(row.incident_date)),
                    Text(unicode(row.type)),
                    Text(unicode(row.encounter.encounter_date)),
                    Text(unicode(row.encounter.patient.chw))])
