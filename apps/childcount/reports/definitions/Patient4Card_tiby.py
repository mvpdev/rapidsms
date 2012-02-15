#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section

from childcount.models import Patient, CHW
from locations.models import Location

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport
from childcount.reports.definitions import patients_toolbox as tb
from childcount.reports.definitions import tiby


def add_chw_row(table, chw):

    empty = Text("")
    table.add_row([Text(':%s_%s' % (chw.location.code, chw.username)), \
                   Text(chw.__unicode__(), bold=True, size=16), \
                   empty, empty, empty, empty, empty])


class Report(PrintedReport):
    """ list all patients registered on the dashboard """
    title = 'ID ASSIGNEMENT SHEET'
    filename = 'Patient4Card_tiby'
    formats = ['html', 'pdf', 'xls']
    argvs = []


    def generate(self, rformat, title, filepath, data):

        self.chw_map = tiby.chw_map

        doc = Document(title)

        table = tb._create_patient_table()

        chews = CHW.objects.all()
        for chw in chews:
            patients = Patient.objects.filter(chw=chw)\
                                      .order_by('household', 'id')
            if patients.count() == 0:
                continue

            add_chw_row(table, chw)

            for patient in patients:
                self.add_patient_to_table(table, patient)
            
        doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def add_patient_to_table(self, table, patient, only_hohh=False):
        """ add patient to table """
        is_bold = is_hohh = patient.is_head_of_household()

        if only_hohh and not is_hohh:
            return

        try:
            hh = patient.household.health_id.upper()
        except:
            hh = u""

        if only_hohh:
            hh = u"%d" % Patient.objects.filter(household=patient).count()
            is_bold = False

        dob = patient.dob.strftime('%d.%m.%Y')
        if patient.estimated_dob:
            dob = u"%s*" % dob

        location = u"%(village)s/%(code)s-%(chw)s" \
                   % {'village': patient.location.name.title(), \
                      'code': patient.location.code.upper(), \
                      'chw': patient.chw.id.__str__().zfill(3)}

        if self.chw_map:
            try:
                loc_start, chwid = location.rsplit('-', 1)
                location = u"%s-%s" % (loc_start, self.chw_map[int(chwid)])
            except:
                pass

        table.add_row([
            Text(patient.health_id.upper(), bold=is_bold),
            Text(patient.full_name(), bold=is_bold),
            Text(dob, bold=is_bold),
            Text(patient.gender, bold=is_bold),
            Text(location, bold=is_bold),
            Text(hh, bold=is_bold),
            Text(patient.location.name.upper(), bold=is_bold)])
