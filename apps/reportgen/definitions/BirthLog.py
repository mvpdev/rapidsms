#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Text, Paragraph

from locations.models import Location
from childcount.models import BirthReport

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

_variants = [('All Locations', 'all', {'loc_pk': 0})]
_locations = [(loc.name, loc.code, {'loc_pk': loc.pk}) \
                            for loc in Location.objects.all()]
_variants.extend(_locations)


class ReportDefinition(PrintedReport):
    """ list all Births """
    title = 'Birth Log'
    filename = 'birth_log'
    formats = ['html', 'pdf', 'xls']
    variants = _variants

    def generate(self, period, rformat, title, filepath, data):
        doc = Document(title)

        if 'loc_pk' not in data or data['loc_pk'] == 0:
            reports = BirthReport.objects.all()\
                .order_by('encounter__patient__location', 'encounter__chw',
                          'encounter__encounter_date')
        else:
            loc_pk = data['loc_pk']
            reports = BirthReport.objects\
                .filter(encounter__patient__location__pk=loc_pk)\
                .order_by('encounter__patient__location', 'encounter__chw',
                          'encounter__encounter_date')
        reports = reports.filter(
            encounter__encounter_date__gte=period.start,
            encounter__encounter_date__lte=period.end
        )
        doc.add_element(
            Paragraph(_(u"From: %(start)s to %(end)s." %
                        {'start': period.start.strftime("%d %B, %Y"),
                         'end': period.end.strftime("%d %B, %Y")})))
        
        current = 0
        total = reports.count() + 1
        self.set_progress(0)
        table = self._create_table()
        for report in reports:
            self._add_report_to_table(table, report)
            current += 1
            self.set_progress(100.0 * current / total)
        doc.add_element(table)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

    def _create_table(self):
        table = Table(11)
        table.add_header_row([
            Text(_(u'LOC')),
            Text(_(u'HID')),
            Text(_(u'Name')),
            Text(_(u'Gen.')),
            Text(_(u'DOB')),
            Text(_(u'Age')),
            Text(_(u'HOH')),
            Text(_(u'Mother\'s HID')),
            Text(_(u'Delivered in Health Facility')),
            Text(_(u'Encounter Date')),
            Text(_(u'CHW'))])

        return table

    def _add_report_to_table(self, table, report):
        """ add report to table """
        patient = report.encounter.patient
        table.add_row([
            Text(patient.location),
            Text(patient.health_id.upper()),
            Text(patient.full_name()),
            Text(patient.gender),
            Text(patient.dob.strftime("%d/%m/%y")),
            Text(patient.humanised_age()),
            Text(patient.household.health_id.upper()),
            Text(patient.mother.health_id.upper()),
            Text(report.clinic_delivery_text),
            Text(report.encounter.encounter_date.strftime("%d/%m/%y")),
            Text(patient.chw)])
