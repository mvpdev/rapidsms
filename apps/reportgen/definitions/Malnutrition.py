#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

from datetime import date, timedelta

from django.utils.translation import ugettext as _
from django.db.models import Q

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from childcount.models import CHW, Clinic
from childcount.models import Patient
from childcount.models.reports import NutritionReport
from childcount.helpers.patient import latest_muac_date, latest_muac_raw

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

class ReportDefinition(PrintedReport):
    title = _(u"Malnutrition Report")
    filename = 'malnutrition'
    formats = ['pdf','html']
    variants = [(c.name, c.code, {'clinic_pk': c.pk}) \
                                for c in Clinic.objects.all()]

    def generate(self, period, rformat, title, filepath, data):
        doc = Document(title)
        doc.add_element(PageBreak())
        if 'clinic_pk' not in data:
            clinic_pk = data['clinic_pk']
            clinics = Clinic.objects.filter(pk=clinic__pk)
        else:
            clinics = Clinic.objects.all()
        total = clinics.count()
        for i,clinic in enumerate(clinics):
            self.set_progress(100.0*i/total)
            
            doc.add_element(Section(clinic.name)) 
           
            t, t2 = self._malnutrition_table(period, clinic)
            doc.add_element(t)
            doc.add_element(t2)
            doc.add_element(PageBreak())

        return render_doc_to_file(filepath, rformat, doc)

    def _malnourished_by_clinic(self, period, clinic):
        under_fives = Patient\
            .objects\
            .filter(chw__clinic=clinic)\
            .muac_eligible(period.start, period.end)\
            .order_by('location__code')

        output = []
        no_report = []
        for u in under_fives:
            try:
                # Get reports with a non-null MUAC or
                # a "YES" Oedema value. Reports with a "NO"
                # oedma value and no MUAC are not helpful.
                r = NutritionReport\
                    .objects\
                    .filter(encounter__chw__clinic=clinic,\
                        encounter__patient=u,
                        encounter__encounter_date__lte=period.end)\
                    .filter((Q(muac__isnull=False)&Q(muac__gt=0)) | \
                            Q(oedema__in=NutritionReport.OEDEMA_YES))\
                    .latest()
            except NutritionReport.DoesNotExist:
                lr = latest_muac_raw(period, u)
                if lr is None:
                    no_report.append(u)
                    continue
                else:
                    r = lr
            r = NutritionReport.objects\
                        .filter(encounter__patient=u).latest()
            # If there's no muac, flag child for muac
            if r.muac is None or r.status is None:
                no_report.append(u)
                continue

            if r.status != NutritionReport.STATUS_HEALTHY:
                output.append(r)
            else:
                # Child is healthy
                pass

            # If the muac figure is old, add this report to the To-do
            # list.
            if (r.encounter.encounter_date + timedelta(90)) <= period.end:
                no_report.append(u)
        
        return (output, no_report)

    def _malnutrition_table(self, period, clinic):
        (malnourished, unknown) = self._malnourished_by_clinic(period, clinic)
        table = Table(8, \
            Text(_(u"Children U5 Flagged as Malnourished as of %s") %
                period.end.strftime("%d %b %Y")))

        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Last MUAC")),
            Text(_(u"MUAC Status")),
            Text(_(u"Od.")),
            Text(_(u"Household Head")),
            Text(_(u"CHW")),
        ])
        table.set_column_width(7, 0)
        table.set_column_width(7, 1)
        table.set_column_width(12, 3)
        table.set_column_width(15, 4)
        table.set_column_width(4, 5)
        for r in malnourished:
            (kid, nut) = (r.encounter.patient, r)

            muac_str = nut.encounter.encounter_date.strftime("%d-%b-%Y")
            if nut.status is not None:
                status_str = nut.verbose_state
            else:
                status_str = _(u'Unknown')

            if nut.muac:
                status_str += u' [%d]' % nut.muac
            else:
                status_str += _(u' -- No MUAC')
            oedema_str = nut.oedema 
                            
            table.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(muac_str),
                Text(status_str),
                Text(oedema_str),
                Text(kid.household.full_name()),
                Text(kid.chw.full_name())
            ])
        
        table2 = Table(6, \
            Text(_(u"Children U5 without MUAC in 90 Days Ending %s") % \
                period.end.strftime("%d %b %Y")))

        table2.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Latest MUAC")),
            Text(_(u"Household Head")),
            Text(_(u"CHW")),
        ])
        table2.set_column_width(7, 0)
        table2.set_column_width(7, 1)
        for kid in unknown:
            table2.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(latest_muac_date(period, kid)),
                Text(kid.household.full_name()),
                Text(kid.chw.full_name())
            ])

        return (table, table2)



