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
    title = 'Patient List'
    filename = 'patient_list_2'
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
            stitle = full_name = chw.full_name()
            if rformat == 'xls':
                stitle = chw.username
                
            doc.add_element(Section(stitle)) 
            # Time period string
            time_string = _(u"For: %s") % time_period.title
            doc.add_element(Paragraph(u"%s: %s; %s" % 
                                (full_name, chw.location, time_string)))
            table = self._create_patient_table()
            self._add_chw_to_table(table, chw)
            doc.add_element(table)

            current += 1
            self.set_progress(100.0*current/total)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

    def _create_patient_table(self):
        table = Table(6)
        table.add_header_row([
            Text(_(u'LOC')),
            Text(_(u'HID')),
            Text(_(u'Name')),
            Text(_(u'Gen.')),
            Text(_(u'Age')),
            Text(_(u'HOH'))])

        return table

    def _add_chw_to_table(self, table, chw):
        """ add chw to table """
       
        l = chw.location or chw.clinic
        if l:
            location = u"%(village)s/%(code)s" \
                       % {'village': l.name.title(),
                          'code': l.code.upper()}
        else:
            location = u"--"
        households = chw\
                .patient_set\
                .filter(pk=F('household__pk'))\
                .order_by('location__code','last_name')
        for household in households:
            table.add_row([
                Text(household.location, bold=True),
                Text(household.health_id.upper(), bold=True),
                Text(household.full_name(), bold=True),
                Text(household.gender, bold=True),
                Text(household.humanised_age(), bold=True),
                Text(u"HOH", bold=True)])
            hs = chw\
                    .patient_set\
                    .filter(household=household)\
                    .exclude(health_id=household.health_id)\
                    .order_by('last_name')\
                    .filter(status=Patient.STATUS_ACTIVE)
            for patient in hs:
                table.add_row([
                    Text(patient.location),
                    Text(patient.health_id.upper()),
                    Text(patient.full_name()),
                    Text(patient.gender),
                    Text(patient.humanised_age()),
                    Text(u"")])
