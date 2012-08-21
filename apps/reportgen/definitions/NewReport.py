#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: Katembu

import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db.models import F
from django.utils.translation import ugettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section, Paragraph

from locations.models import Location
from childcount.models import CHW, Patient

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
    title = 'New Patient List'
    filename = 'patient_list_2'
    formats = ['xls']
    variants = _variants

    def generate(self, time_period, rformat, title, filepath, data):
        doc = Document(title)

        current = 0
        chws = ['child', 'hoh', 'pregnancy']
        total = 3 + 1
        self.set_progress(0)
        for chw in chws:
            stitle = full_name = chw
            if rformat == 'xls':
                stitle = chw

            doc.add_element(Section(stitle))
            # Time period string
            table = self._create_patient_table()
            self._add_data_to_table(table, chw)
            doc.add_element(table)

            current += 1
            self.set_progress(100.0*current / total)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

    def _create_patient_table(self):
        table = Table(12)
        table.add_header_row([
            Text(_(u'location')),
            Text(_(u'hid')),
            Text(_(u'first_name')),
            Text(_(u'last_name')),
            Text(_(u'gender')),
            Text(_(u'bod')),
            Text(_(u'edob')),
            Text(_(u'age')),
            Text(_(u'hoh')),
            Text(_(u'chw')),
            Text(_(u'chwname')),
            Text(_(u'commcare_id'))])

        return table

    def _add_data_to_table(self, table, schw):
        """ add data to table """

        if schw == 'hoh':
            households = Patient.objects.filter(pk=F('household__pk'),
                 status=Patient.STATUS_ACTIVE)\
                .order_by('chw', 'location__code')
        if schw == 'child':
            under_five = date.today() - timedelta(days=5*365)
            households = Patient.objects.filter(
                            status=Patient.STATUS_ACTIVE,
                            dob__gte=under_five)\
                .order_by('chw', 'location__code')

        if schw == 'pregnancy':
            end = datetime.now()
            start = end - relativedelta(months=9)
            households = Patient.objects.all() \
                            .order_by('chw', 'location__code') \
                            .pregnant(start, end)

        for household in households:
            try:
                hh = household.household.health_id.upper()
            except:
                hh = "UNKNOWN"
            table.add_row([
                Text(household.location.name, bold=True),
                Text(household.health_id.upper(), bold=True),
                Text(household.first_name, bold=True),
                Text(household.last_name, bold=True),
                Text(household.get_gender_display().lower(), bold=True),
                Text(household.dob, bold=True),
                Text(household.estimated_dob, bold=True),
                Text(household.humanised_age(), bold=True),
                Text(hh, bold=True),
                Text(household.chw.alias, bold=True),
                Text(household.chw.full_name(), bold=True),
                Text("", bold=True)])
