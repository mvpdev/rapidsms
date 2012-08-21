
from django.db.models import Q
from django.db.models.aggregates import Count
from django.utils.translation import ugettext as _ 

from ccdoc import Document, Table, Paragraph, Text

from reporters.models import Reporter

from logger_ng.models import LoggedMessage

from reportgen.PrintedReport import PrintedReport
from reportgen.utils import render_doc_to_file

FILTER_A = Q(text__contains=_("You successfuly registered "))
FILTER_B = Q(text__regex=_(".*\+V.*Successfully processed\: \[.*"))
FILTER_C = Q(text__contains=_("Successfully processed: [")) & \
    (Q(text__contains="+U ") | \
    Q(text__contains="+S ") | \
    Q(text__contains="+P ") | \
    Q(text__contains="+N ") | \
    Q(text__contains="+T ") | \
    Q(text__contains="+M ") | \
    Q(text__contains="+F ") | \
    Q(text__contains="+G ") | \
    Q(text__contains="+R "))

class ReportDefinition(PrintedReport):
    title = _('Data Entry Statistics')
    filename = 'stats_form_'
    formats = ['pdf','xls','html']

    variants = [
        (_("Form A (Registration)"),   "a", {'look_for': FILTER_A}),
        (_("Form B (HH Visit)"),       "b", {'look_for': FILTER_B}),
        (_("Form C (Consultation)"),   "c", {'look_for': FILTER_C}),
    ]

    def generate(self, period, rformat, title, filepath, data):

        def _t(string):
            return Text(_(unicode(string)))

        self.set_progress(0.0)
        doc = Document(self.title, _("For: ")+period.title, landscape=True)

        # Get all of the reporters who have messages
        reporters = Reporter\
            .objects\
            .annotate(c=Count('loggedmessage'))\
            .filter(c__gt=0)\
            .order_by('first_name')


        # We first get all of the message counts into a dictionary
        count_data = {}
        total = reporters.count()+1
        for i,r in enumerate(reporters):
            count_data[r] = [self._count(p, r, data['look_for']) \
                        for p in period.sub_periods()]
            self.set_progress((100.0*i)/(total))

        # Filter out the users who haven't sent anything
        have_data = filter(lambda x: sum(count_data[x]), count_data)

        reporters = reporters\
            .filter(pk__in=have_data)\
            .order_by('first_name')

        t = Table(len(have_data)+2)

        header = [_t("Dates")] + [_t(r.full_name()) for r in reporters] + [_t("[Total]")]
        t.add_header_row(header)

        # Turn our dictionary into a Table objects
        for i,p in enumerate(period.sub_periods()):
            row = [Text(p.title)]
            for r in reporters:
                if r in have_data:
                    row.append(Text(count_data[r][i]))

            # Add row total
            row.append(Text(self._count(p, None, data['look_for'])))
            t.add_row(row)

        row = [_t("[All]")]
        for i,r in enumerate(reporters):
            row.append(Text(self._count(period, r, data['look_for'])))
        row.append(Text(self._count(period, None, data['look_for'])))
        t.add_row(row)
            

        doc.add_element(t)
        return render_doc_to_file(filepath, rformat, doc)

    def _count(self, sub_period, reporter, look_for):
        if reporter is not None:
            try:
                identity = reporter\
                    .connections\
                    .get(backend__slug='debackend')\
                    .identity
            except:
                return 0

        l = LoggedMessage\
            .objects\
            .filter(direction=LoggedMessage.DIRECTION_OUTGOING,\
                date__range=(sub_period.start, sub_period.end),
                backend='debackend')\
            .filter(look_for)

        if reporter is None:
            return l.count()
        else:
            return l.filter(identity=identity).count()


