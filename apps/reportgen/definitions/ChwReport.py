#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

import bonjour.dates

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from childcount.models import CHW, Clinic
from childcount.models.reports import ReferralReport
from childcount.models.reports import DangerSignsReport
from childcount.models.reports import NutritionReport
from childcount.models.reports import UnderOneReport
from childcount.models.reports import FollowUpReport

from childcount import helpers

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

class RecentPeriod(object):
    end = datetime.now()
    start = end - timedelta(45)

class ReportDefinition(PrintedReport):
    title = u"CHW Report"
    filename = 'chw_report_'
    formats = ['pdf','html']
    variants = [(c.name, c.code, {'clinic_pk': c.pk}) \
                                for c in Clinic.objects.all()]

    def generate(self, period, rformat, title, filepath, data):
        # Make sure that user passed in a clinic 
        if 'clinic_pk' not in data:
            raise ValueError('You must pass a clinic PK as data')
        clinic_pk = data['clinic_pk']

        self._period = period
        self._sub_periods = period.sub_periods()
        self._ncols = len(self._sub_periods) + 2

        self._indicators = helpers.chw.report_indicators()
        
        doc = Document(title, period.title)
        doc.add_element(PageBreak())

        chws = CHW\
            .objects\
            .filter(clinic__pk=clinic_pk, is_active=True)
        
        total = chws.count()
        for i,chw in enumerate(chws):
            self.set_progress(100.0*i/total)

            doc.add_element(Section(chw.full_name())) 
           
            # Time period string
            doc.add_element(Paragraph(_(u"For: %s") % period.title))

            doc.add_element(self._indicator_table(chw))
            doc.add_element(self._pregnancy_table(chw))
            doc.add_element(self._follow_up_table(chw))
            doc.add_element(self._muac_table(chw))
            doc.add_element(self._immunization_table(chw))

            doc.add_element(PageBreak())

        return render_doc_to_file(filepath, rformat, doc)

    def _indicator_table(self, chw):
        table = Table(self._ncols, title=Text(_(u"Indicators")))

        headers = [_(u"Indicator")]
        headers += [sp.title for sp in self._period.sub_periods()]
        headers += [_(u"Tot/Avg")]

        table.add_header_row(map(Text, headers))

        for i in xrange(0, len(self._sub_periods)):
            table.set_column_width(12, i+1)
        table.set_column_width(18, self._ncols-1)

        patients = chw.patient_set.all()

        # For each group of indicators...
        for group in self._indicators:
            table.add_row([Text(" ")] * self._ncols)

            title_row = [Text(group['title'], bold=True)]
            title_row += [Text("")] * (self._ncols - 1)

            table.add_row(title_row)

            # For each individual indicator...
            for ind in group['columns']:
                data_row = [Text(ind['name'])]

                data_row += [Text(ind['ind'](sp, patients)) \
                    for sp in self._sub_periods]
                data_row += [Text(ind['ind'](self._period, patients))]

                table.add_row(data_row)
        return table 

    def _follow_up_table(self, chw):
        table = Table(7, \
            Text(_(u"Patients Referred in the Previous 45 days "\
                "(or Given Medicine) and "\
                "Lacking an On-Time Follow-Up Visit")))
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Household Head")),
            Text(_(u"Event / Date")),
            Text(_(u"Danger Signs")),
            Text(_(u"Follow-Up Date")),
        ])

        for entry in self._lacking_follow_up(RecentPeriod, chw):
            patient = entry['patient']
            ref = entry['referral']
            ds = entry['danger_signs']
            fu = entry['follow_up']
          
            if ref is None:
                urgency_str = "[No Referral]" 
            else:
                urgency_str = ref.verbose_urgency + _(' on ') + \
                    bonjour.dates.format_date(ref.encounter.encounter_date, \
                        format='medium')

            table.add_row([
                Text(patient.location.code),
                Text(patient.health_id.upper()),
                Text(patient.full_name() + u" / " + \
                                    patient.humanised_age()),
                Text(patient.household.full_name()),
                Text(urgency_str),
                Text(u", ".join([sign.description \
                                    for sign in ds.danger_signs.all()]))
                    if ds else Text(_(u"[No DSs Reported]")),
                Text(_(u"Late: ") + bonjour.dates.format_date(fu\
                            .encounter\
                            .encounter_date, format='medium'))\
                    if fu else Text(_(u"[No Follow-Up]"))])

        return table


    def _immunization_table(self, chw):
        table = Table(5, \
            Text(_(u"Children Under 5 Without Known "\
                    "Up-to-date Immunizations")))

        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Latest Imm. Report")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        for kid in helpers.chw.kids_needing_immunizations(RecentPeriod, chw):
            im = helpers.patient.latest_imm_report(RecentPeriod, kid)
            if im is None:
                im_str = _(u"[No Report]")
            else:
                im_stat = filter(lambda x: x[0] == im.immunized,\
                    UnderOneReport.IMMUNIZED_CHOICES)[0][1]
                im_str = _(u"Reported \"%(status)s\" on %(date)s") % \
                    {'status': im_stat,\
                    'date': bonjour.dates.format_date(im.encounter.encounter_date, format='medium')}

            table.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(im_str),
                Text(kid.household.full_name())])
                
        return table

    def _pregnancy_table(self, chw):
        table = Table(6, \
            Text(_(u"Women in 2nd and 3rd Trimester "\
                    "who haven't had ANC in 5 Weeks")))
        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Last ANC")),
            Text(_(u"Approx Due Date")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.set_column_width(12, 3)
        table.set_column_width(12, 4)

        for pair in helpers.chw.pregnant_needing_anc(RecentPeriod, chw):
            (woman, last_anc, due_date) = pair
            table.add_row([
                Text(woman.location.code),
                Text(woman.health_id.upper()),
                Text(woman.full_name() + u" / " + woman.humanised_age()),
                Text('No ANC' if last_anc is None else \
                    bonjour.dates.format_date(last_anc, format='medium')),
                Text(bonjour.dates.format_date(due_date, format='medium')),
                Text(woman.household.full_name())])
        return table                

    def _muac_table(self, chw):
        table = Table(7, \
            Text(_(
            u"Children without MUAC in past 1 month (SAM) " \
            "or 3 months (healthy)")))

        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Last MUAC")),
            Text(_(u"MUAC Status")),
            Text(_(u"Od.")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.set_column_width(15, 3)
        table.set_column_width(15, 4)
        table.set_column_width(5, 5)

        for row in helpers.chw.kids_needing_muac(RecentPeriod, chw):
            (kid, nut) = row

            muac_str = status_str = _(u'[No MUAC]')
            oedema_str = _(u'U')
            if nut is not None:
                muac_str = bonjour.dates.format_date(nut.encounter.encounter_date, format='medium')
                status_str = _(u'%(status)s [%(muac)d]') % \
                    {'status': nut.verbose_state, 
                    'muac': nut.muac}
                oedema_str = nut.oedema 
                            

            table.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(muac_str),
                Text(status_str),
                Text(oedema_str),
                Text(kid.household.full_name())
            ])

        return table

    def _lacking_follow_up(self, period, chw):
        """People lacking follow-up in last 45 days
        """
        (late, never) = helpers.chw.people_without_follow_up(period, chw)
       
        entries = []
        for ref in (late+never):
            entries.append(self._dict_for_follow_up(ref))

        return entries


    def _dict_for_follow_up(self, elig):
        all_ds = DangerSignsReport\
            .objects\
            .filter(encounter=elig.encounter)

        ds = all_ds[0] if (all_ds.count() > 0) else None

        all_fu = FollowUpReport\
            .objects\
            .filter(encounter__patient=elig.encounter.patient, \
                encounter__encounter_date__gt=\
                    elig.encounter.encounter_date)\
            .order_by('encounter__encounter_date')

        fu = all_fu[0] if (all_fu.count() > 0) else None

        all_ref = ReferralReport\
            .objects\
            .filter(encounter=elig.encounter)

        ref = all_ref[0] if (all_ref.count() > 0) else None

        return {
            'patient': elig.encounter.patient,
            'referral': ref,
            'danger_signs': ds,
            'follow_up': fu,
            }
        
