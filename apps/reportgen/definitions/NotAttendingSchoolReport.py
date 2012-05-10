#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import time
from datetime import date

from django.db.models import F
from django.utils.translation import ugettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section, Paragraph

from locations.models import Location
from childcount.models import CHW, Patient, SchoolAttendanceReport

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

_variants = [('All Locations', 'all', {'loc_pk': 0})]
_chw_locations = CHW.objects.values('location').distinct()
_locations = [(loc.name, loc.code, {'loc_pk': loc.pk}) \
                            for loc in Location.objects\
                                                .filter(pk__in=_chw_locations)]
_variants.extend(_locations)


class ReportDefinition(PrintedReport):
    title = 'Children Not Attending School'
    filename = 'children_not_attending_school'
    formats = ['html', 'pdf', 'xls']
    variants = _variants

    def generate(self, time_period, rformat, title, filepath, data):
        doc = Document(title)

        if 'loc_pk' not in data:
            chws = CHW.objects.all().order_by('id', 'first_name', 'last_name')
        elif data['loc_pk'] == 0:
            chws = CHW.objects.all().order_by('id', 'first_name', 'last_name')
        else:
            loc_pk = data['loc_pk']
            chws = CHW.objects\
                        .filter(location__pk=loc_pk)\
                        .order_by('id', 'first_name', 'last_name')
                        
        # table = self._create_chw_table()
        
        current = 0
        total = chws.count() + 1
        self.set_progress(0)
        for chw in chws:
            if SchoolAttendanceReport\
                    .objects\
                    .filter(household_pupil__gt=F('attending_school'), \
                    encounter__chw=chw).count() == 0:
                continue
            stitle = full_name = chw.full_name()
            if rformat == 'xls':
                stitle = chw.username
                
            doc.add_element(Section(stitle)) 
            # Time period string
            time_string = _(u"For: %s") % time_period.title
            doc.add_element(Paragraph(u"%s; %s" % (full_name, time_string)))
            table = self._create_table()
            self._add_chw_to_table(table, chw)
            doc.add_element(table)

            current += 1
            self.set_progress(100.0 * current/total)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

    def _create_table(self):
        table = Table(4)
        table.add_header_row([
            Text(_(u'LOC')),
            Text(_(u'HID')),
            Text(_(u'Name')),
            Text(_(u'# Not Attending'))])

        return table

    def _add_chw_to_table(self, table, chw):
        """ add chw to table """
        reports = SchoolAttendanceReport\
                    .objects\
                    .filter(household_pupil__gt=F('attending_school'), \
                    encounter__chw=chw)
        for report in reports:
            not_attending = report.household_pupil - report.attending_school
            table.add_row([
                Text(report.encounter.patient.location),
                Text(report.encounter.patient.health_id.upper()),
                Text(report.encounter.patient.full_name()),
                Text(not_attending)])
