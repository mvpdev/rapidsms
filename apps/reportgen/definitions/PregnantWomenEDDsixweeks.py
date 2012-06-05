#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from datetime import date
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from locations.models import Location

from childcount.models import CHW, AntenatalVisitReport, Patient

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

_variants = [('All Locations', '_all', {'loc_pk': 0})]
_chew_locations = CHW.objects.values('location').distinct()
_locations = [(loc.name, '_%s' % loc.code, {'loc_pk': loc.pk}) \
                            for loc in Location.objects\
                                                .filter(pk__in=_chew_locations)]
_variants.extend(_locations)


class ReportDefinition(PrintedReport):
    title = _(u"Pregnancy Women with EDD of less than 6 weeks")
    filename = 'PregnantWomenEDDsixweeks'
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
        end_date = period.start + relativedelta(weeks=6)
        start_date = period.start
        
        for chw in chws:
            plist = AntenatalVisitReport.objects.filter(\
                            expected_on__lt=end_date,
                            expected_on__gt=start_date,
                            encounter__patient__chw=chw,
                            encounter__patient__status=Patient.STATUS_ACTIVE)
            if plist:

                t = Table(5)
                t.add_header_row([
                    Text(unicode(_(u"Date Recorded"))),
                    Text(unicode(_(u"Patient"))),
                    Text(unicode(_(u"EDD"))),
                    Text(unicode(_(u"CHW"))),
                    Text(unicode(_(u"Location")))])
                for row in plist:
                    t.add_row([
                        Text(unicode(row.encounter.encounter_date.strftime('%d-%m-%Y'))),
                        Text(unicode(row.encounter.patient)),
                        Text(unicode(row.expected_on)),
                        Text(unicode(row.encounter.patient.chw)),
                        Text(unicode(row.encounter.patient.chw.location))])
                doc.add_element(t)
                # doc.add_element(PageBreak())
                current += 1
                self.set_progress(100.0*current/total)
        return render_doc_to_file(filepath, rformat, doc)
