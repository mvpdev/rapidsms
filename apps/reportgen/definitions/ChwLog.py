#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

from datetime import date

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from locations.models import Location

from childcount.models import CHW, Encounter, Patient
from childcount.models.reports import NutritionReport, SPregnancy, \
    AppointmentReport, FeverReport, UnderOneReport, SUnderOne, \
    DangerSignsReport, MedicineGivenReport, ReferralReport, \
    HouseholdVisitReport, FamilyPlanningReport, PregnancyReport, \
    NeonatalReport, FollowUpReport

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

_variants = [('All Locations', '_all', {'loc_pk': 0})]
_chew_locations = CHW.objects.values('location').distinct()
_locations = [(loc.name, '_%s' % loc.code, {'loc_pk': loc.pk}) \
                            for loc in Location.objects\
                                                .filter(pk__in=_chew_locations)]
_variants.extend(_locations)


class ReportDefinition(PrintedReport):
    title = _(u"CHW Log ")
    filename = 'chw_log'
    formats = ['pdf', 'html', 'xls']
    variants = _variants

    def generate(self, period, rformat, title, filepath, data):
        doc = Document(title, landscape=True, stick_sections=True)
        if 'loc_pk' not in data:
            raise ValueError('You must pass a Location PK as data')
        elif data['loc_pk'] == 0:
            chws = CHW.objects.all().order_by('location', 'id', \
                                                'first_name', 'last_name')
        else:
            loc_pk = data['loc_pk']
            chws = CHW.objects.filter(location__pk=loc_pk)\
                                .order_by('id', 'first_name', 'last_name')
        if not chws:
            return
        current = 0
        total = chws.count() + 1
        self.set_progress(0)
        for chw in chws:
            encounters = Encounter.objects\
                                .filter(encounter_date__gte=period.start, \
                                encounter_date__lte=period.end, \
                                patient__status = Patient.STATUS_ACTIVE, \
                                patient__chw=chw).order_by('encounter_date')
            if encounters:
                doc.add_element(Section(u"%s: %s" % (chw, chw.location.name), section_name=chw.username))
                doc.add_element(Paragraph(u"Period: %s to %s" % \
                                        (period.start.strftime("%d %B, %Y"), \
                                        period.end.strftime("%d %B, %Y"))))
                # children
                children = encounters\
                        .filter(patient__dob__gt=date(period.end.year - 5, \
                                                        period.end.month, 1))
                if children:
                    doc.add_element(Paragraph(_(u'CHILDREN')))
                    
                    table1 = self._children_table()
                    table1 = self._children_table_data(table1, children)

                    doc.add_element(table1)
                women = PregnancyReport.objects\
                            .filter(encounter__pk__in=encounters.values('pk'))\
                            .order_by('encounter__encounter_date')
                if women:
                    doc.add_element(Paragraph(_(u'PREGNANT WOMEN')))
                    
                    table2 = self._women_table()
                    table2 = self._women_table_data(table2, women)
                    doc.add_element(table2)
                households = encounters.filter(type=Encounter.TYPE_HOUSEHOLD)\
                            .order_by('encounter_date')
                if households:
                    doc.add_element(Paragraph(_(u'HOUSEHOLD')))
                    
                    table3 = self._household_table()
                    table3 = self._household_table_data(table3, households)
                    doc.add_element(table3)
                
                # table = self._generate_chw_table_data(chw, encounters)
                # doc.add_element(PageBreak())
                current += 1
                self.set_progress(100.0*current/total)
        return render_doc_to_file(filepath, rformat, doc)


    def _create_chwlog_table(self):
        table = Table(5)
        table.add_header_row([
            Text(_(u'Date')),
            Text(_(u'Name')),
            Text(_(u'HID')),
            Text(_(u'Reports')),
            Text(_(u'Comments'))])
        # column alignments
        table.set_alignment(Table.ALIGN_LEFT, column=0)
        table.set_alignment(Table.ALIGN_LEFT, column=1)
        table.set_alignment(Table.ALIGN_CENTER, column=2)
        table.set_alignment(Table.ALIGN_RIGHT, column=3)
        table.set_alignment(Table.ALIGN_RIGHT, column=4)
        # column sizings
        table.set_column_width(10, column=0)
        table.set_column_width(7, column=2)

        return table

    def _generate_chw_table_data(self, chw, encounters):
        table = self._create_chwlog_table()
        for encounter in encounters:
            patient = encounter.patient
            rpts = encounter.ccreport_set.all()
            result = self._explode_ccreports(rpts)
            reports = u', '.join([c.__class__.__name__ \
                                for c in encounter.ccreport_set.all()])
            table.add_row([Text(u"%s" \
                    % encounter.encounter_date.strftime("%m/%Y")), \
                    Text(u"%s" % patient.full_name()), \
                    Text(u"%s" % patient.health_id.upper()), \
                    Text(reports), \
                    Text(result)])
        return table

    def _explode_ccreports(self, reports):
        result = []
        for rpt in reports:
            if isinstance(rpt, NutritionReport):
                result.append(u"+N %s %s %s" % (rpt.muac, rpt.oedema, \
                                        rpt.verbose_state))
        return u' | ' . join(result)

    def _children_table(self):
        table = Table(13)
        table.add_header_row([
            Text(u'#'),
            Text(_(u'Date')),
            Text(_(u'Name')),
            Text(_(u'Gender')),
            Text(_(u'Age')),
            Text(_(u'Mother')),
            Text(_(u'Next Apt')),
            Text(_(u'RDT+')),
            Text(_(u'MUAC (+/-)')),
            Text(_(u'Immunized')),
            Text(_(u'Danger Signs')),
            Text(_(u'PID')),
            Text(_(u'Forms'))
            ])

        table.set_column_width(2, 0)
        table.set_column_width(6, 1)
        table.set_column_width(14, 2)
        table.set_column_width(5, 3)
        table.set_column_width(5, 4)
        table.set_column_width(13, 5)
        table.set_column_width(3, 6)
        table.set_column_width(4, 7)
        table.set_column_width(10, 8)
        table.set_column_width(13, 9)
        table.set_column_width(10, 10)
        table.set_column_width(5, 11)

        table.set_alignment(Table.ALIGN_LEFT, column=2)
        table.set_alignment(Table.ALIGN_LEFT, column=5)
        table.set_alignment(Table.ALIGN_LEFT, column=8)
        table.set_alignment(Table.ALIGN_LEFT, column=9)
        table.set_alignment(Table.ALIGN_LEFT, column=11)
        table.set_alignment(Table.ALIGN_LEFT, column=12)
        return table

    def _children_table_data(self, table, children):
        num = 0
        for enc in children:
            child = enc.patient
            if child.mother:
                mother = child.mother.full_name()
            else:
                mother = u"-"
            num += 1
            apt = ds = rdt = immunization = muac = u""
            for rpt in enc.ccreport_set.all():
                if isinstance(rpt, NutritionReport):
                    muac = self._child_muac_report(child, rpt)
                if isinstance(rpt, FeverReport):
                    rdt = self._child_fever_report(child, rpt)
                if isinstance(rpt, UnderOneReport):
                    immunization = self._child_immunization_report(child, rpt)
                if isinstance(rpt, DangerSignsReport):
                    ds = self._dangersigns_report(child, rpt)
                if isinstance(rpt, AppointmentReport):
                    apt = self._appointment_report(child, rpt)
            reports = self._encounter_forms(enc)
            table.add_row([
                Text(num),
                Text(enc.encounter_date.strftime("%m/%Y")),
                Text(child.full_name()),
                Text(child.gender),
                Text(child.humanised_age()),
                Text(mother),
                Text(apt),
                Text(rdt),
                Text(muac),
                Text(immunization),
                Text(ds),
                Text(child.health_id.upper()),
                Text(reports)
                ])
        return table

    def _child_muac_report(self, child, report):
        try:
            last_muac = NutritionReport.objects\
                .filter(encounter__patient=child,\
                encounter__encounter_date__lt=report.encounter.encounter_date)\
                .latest()
        except NutritionReport.DoesNotExist:
            pass
        else:
            if last_muac.muac and report.muac is not None \
                                            and last_muac.muac is not None:
                mdiff = report.muac - last_muac.muac
                if mdiff > 0:
                    return u"%s %d (+%d)" % (report.verbose_state, report.muac, \
                                                mdiff)
                else:
                    return u"%s %d (%d)" % (report.verbose_state, report.muac, \
                                                mdiff)
        if report.muac is None and report.weight is not None:
            return u"%s kg." % report.weight
        elif report.muac is None:
            return u""
        return u"%s %d" % (report.verbose_state, report.muac)

    def _child_fever_report(self, child, report):
        return report.rdt_result

    def _appointment_report(self, child, report):
        return report.appointment_date.strftime("%d/%m/%y")

    def _child_immunization_report(self, child, report):
        if isinstance(report, SUnderOne):
            vcodes = u", " .join([v.code.upper() for v in report.vaccine.all()])
            return u"%s: %s" % (report.immunized, vcodes)
        return report.immunized

    def _dangersigns_report(self, child, report):
        return u", " .join([v.code.upper() for v in report.danger_signs.all()])

    def _encounter_forms(self, encounter):
        forms = []
        for rpt in encounter.ccreport_set.all():
            if isinstance(rpt, NutritionReport):
                forms.append(u"+N")
            if isinstance(rpt, FeverReport):
                forms.append(u"+F")
            if isinstance(rpt, UnderOneReport):
                forms.append(u"+T")
            if isinstance(rpt, DangerSignsReport):
                forms.append(u"+S")
            if isinstance(rpt, MedicineGivenReport):
                forms.append(u"+G")
            if isinstance(rpt, NeonatalReport):
                forms.append(u"+N")
            if isinstance(rpt, FollowUpReport):
                forms.append(u"+U")
            if isinstance(rpt, ReferralReport):
                forms.append(u"+R")
            if isinstance(rpt, HouseholdVisitReport):
                forms.append(u"+V")
            if isinstance(rpt, FamilyPlanningReport):
                forms.append(u"+FP")
            if isinstance(rpt, PregnancyReport):
                forms.append(u"+P")
            if isinstance(rpt, AppointmentReport):
                forms.append(u"+AP")
        return u" " . join(forms)

    def _women_table(self):
        table = Table(11)
        table.add_header_row([
            Text(u'#'),
            Text(_(u'Date')),
            Text(_(u'Name')),
            Text(_(u'Gender')),
            Text(_(u'Age')),
            Text(_(u'Next Apt')),
            Text(_(u'Month')),
            Text(_(u'# ANC Visits')),
            Text(_(u'Danger Signs')),
            Text(_(u'PID')),
            Text(_(u'Forms'))
            ])

        table.set_column_width(2, 0)
        table.set_column_width(6, 1)
        table.set_column_width(14, 2)
        table.set_column_width(5, 3)
        table.set_column_width(5, 4)
        table.set_column_width(13, 5)
        table.set_column_width(3, 6)
        # table.set_column_width(4, 7)
        # table.set_column_width(10, 8)

        table.set_alignment(Table.ALIGN_LEFT, column=2)
        table.set_alignment(Table.ALIGN_LEFT, column=5)
        table.set_alignment(Table.ALIGN_LEFT, column=8)
        return table

    def _women_table_data(self, table, preg_reports):
        num = 0
        for prpt in preg_reports:
            woman = prpt.encounter.patient
            enc = prpt.encounter
            num += 1
            apt = ds = month = visits = u""
            for rpt in enc.ccreport_set.all():
                if isinstance(rpt, PregnancyReport):
                    month, visits = self._woman_pregnancy_report(woman, rpt)
                if isinstance(rpt, DangerSignsReport):
                    ds = self._dangersigns_report(woman, rpt)
                if isinstance(rpt, AppointmentReport):
                    apt = self._appointment_report(woman, rpt)
            reports = self._encounter_forms(enc)
            table.add_row([
                Text(num),
                Text(enc.encounter_date.strftime("%m/%Y")),
                Text(woman.full_name()),
                Text(woman.gender),
                Text(woman.humanised_age()),
                Text(apt),
                Text(month),
                Text(visits),
                Text(ds),
                Text(woman.health_id.upper()),
                Text(reports)
                ])
        return table

    def _woman_pregnancy_report(self, woman, report):
        return report.pregnancy_month, report.anc_visits

    def _household_table(self):
        table = Table(8)
        table.add_header_row([
            Text(u'#'),
            Text(_(u'Date')),
            Text(_(u'Household')),
            Text(_(u'Available')),
            Text(_(u'# Children')),
            Text(_(u'Counseling')),
            Text(_(u'PID')),
            Text(_(u'Forms'))
            ])

        table.set_column_width(2, 0)
        table.set_column_width(6, 1)
        table.set_column_width(14, 2)

        table.set_alignment(Table.ALIGN_LEFT, column=2)
        table.set_alignment(Table.ALIGN_LEFT, column=5)
        return table

    def _household_table_data(self, table, encounters):
        num = 0
        for enc in encounters:
            num += 1
            household = enc.patient
            avail = children = advice = visits = u""
            for rpt in enc.ccreport_set.all():
                if isinstance(rpt, HouseholdVisitReport):
                    if rpt.available:
                        avail = u'Y'
                    else:
                        avail = u'N'
                    children = rpt.children
                    advice = u" " . join([c.code.upper() \
                                            for c in rpt.counseling.all()])
                if isinstance(rpt, FamilyPlanningReport):
                    pass
            reports = self._encounter_forms(enc)
            table.add_row([
                Text(num),
                Text(enc.encounter_date.strftime("%m/%Y")),
                Text(household.full_name()),
                Text(avail),
                Text(children),
                Text(advice),
                Text(household.health_id.upper()),
                Text(reports)
                ])
        return table
