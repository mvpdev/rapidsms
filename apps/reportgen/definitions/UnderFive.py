#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from datetime import date
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from locations.models import Location

from childcount.models import CHW, PregnancyReport, Patient

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

_variants = [('All Locations', '_all', {'loc_pk': 0})]
_chew_locations = CHW.objects.values('location').distinct()
_locations = [(loc.name, '_%s' % loc.code, {'loc_pk': loc.pk}) \
                            for loc in Location.objects\
                                    .filter(pk__in=_chew_locations)]
_variants.extend(_locations)


class ReportDefinition(PrintedReport):
    title = _(u"Pregnancy Report")
    filename = 'PregnancyReport'
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

        t = Table(4)
        t.add_header_row([
                    Text(_(u'HID')),
                    Text(_(u'Name')),
                    Text(_(u'Gen.')),
                    Text(_(u'Age'))])

        for chw in chws:
            plist = Patient.objects.filter(\
                            encounter__encounter_date__lte=period.end,
                            encounter__encounter_date__gte=period.start,
                            encounter__patient__chw=chw,
                            encounter__patient__status=Patient.STATUS_ACTIVE)\
                            .under_five(period.end,period.start)

            if plist:
                for row in plist:
                    t.add_row([
                        Text(unicode(row.health_id.upper())),
                        Text(unicode(row.full_name())),
                        Text(unicode(row.gender)),
                        Text(unicode(row.patient.age))])
                        
                # doc.add_element(PageBreak())
                current += 1
                self.set_progress(100.0*current/total)
                
        doc.add_element(t)
        return render_doc_to_file(filepath, rformat, doc)
