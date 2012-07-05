#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: tief

import sys

from django.utils.translation import ugettext as _

from ccdoc import Document, Table, Text, Section

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

from childcount.indicators import birth
from childcount.indicators import death
from childcount.indicators import family_planning
from childcount.indicators import pregnancy
from childcount.indicators import under_one
from childcount.indicators import nutrition
from childcount.indicators import fever
from childcount.indicators import registration
from childcount.indicators import danger_signs
from childcount.indicators import neonatal
from childcount.indicators import referral
from childcount.indicators import follow_up
from childcount.indicators import household
from childcount.indicators import bed_net_coverage
from childcount.indicators import bed_net_utilization
from childcount.indicators import bed_net_utilization_pregnancy as bednet_p
from childcount.indicators import school_attendance
from childcount.indicators import sanitation
from childcount.indicators import drinking_water

from childcount.models import Patient

class ReportDefinition(PrintedReport):
    title = _('MVIS Indicators Two')
    filename = 'MvisIndicatorsTwo'
    formats = ['html', 'pdf', 'xls']

    _indicators = (
        (_("Under Five"), (
            registration.HasUnderFive,
            household.UnderFiveUnique_visit,
        )),
        (_("Neonatal"), (
            registration.HasNeonatal,
            household.NeonatalUnique_visit,
        )),
        (_("Pregnancy"), (
            registration.HasPregnancy,
            household.PregnancyUnique_visit,
        )),
    )

    def generate(self, time_period, rformat, title, filepath, data):
        doc = Document(title, landscape=True)

        self.set_progress(0)
        total = len(self._indicators)

        # Category, Descrip, Sub_Periods
        sub_periods = time_period.sub_periods()
        table = Table(3+len(sub_periods), \
            Text(_("MVIS Indicators (NEW): %s") % time_period.title))

        table.add_header_row([
                Text(_("Category")), 
                Text(_("Sub-Category")), 
                Text(_("Indicator"))] + \
            [Text(p.title) for p in time_period.sub_periods()])

        n_inds = sum([len(i[1]) for i in self._indicators])+1
        count = 0

        patients = Patient.objects.all()
        for i,category in enumerate(self._indicators):
            for ind in category[1]:
                row = []
                row.append(unicode(category[0]))
                row.append(unicode(sys.modules[ind.__module__].NAME))
                row.append(unicode(ind.short_name))

                for t in sub_periods:
                    print "Indicator %s.%s in %s - %s" % \
                        (str(ind.__module__), ind.slug, t.start, t.end)
                    row.append(ind(t, patients))
          
                table.add_row([Text(c) for c in row])

                self.set_progress(100.0*count/n_inds)
                count += 1

        doc.add_element(table)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval
