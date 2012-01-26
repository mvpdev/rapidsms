#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: katembu

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from childcount.models import CHW
from childcount.commands import CCCommand
from childcount.utils import authenticated

from childcount.indicators import nutrition
from childcount.indicators import household
from childcount.indicators import fever
from childcount.indicators import registration

from reportgen.timeperiods import TwelveMonths

class LastSevenDays(object):
    end = datetime.today()
    start = end - timedelta(7)

class ActivityCommand(CCCommand):

    KEYWORDS = {
        'en': ['activity'],
        'rw': ['activity'],
        'fr': ['activity'],
    }

    WEEK = {
        'en': 'week',
        'rw': 'week',
        'fr': 'semaine',
    }

    MONTH = {
        'en': 'month',
        'rw': 'month',
        'fr': 'mois',
    }
    
    MONTHS = {
        'en': {
            'jan': 0,
            'feb': 1,
            'mar': 2,
            'apr': 3,
            'may': 4,
            'jun': 5,
            'jul': 6,
            'aug': 7,
            'sep': 8,
            'oct': 9,
            'nov': 10,
            'dec': 11,
        },

        'rw': {
            'jan': 0,
            'feb': 1,
            'mar': 2,
            'apr': 3,
            'may': 4,
            'jun': 5,
            'jul': 6,
            'aug': 7,
            'sep': 8,
            'oct': 9,
            'nov': 10,
            'dec': 11,
        },

        'fr': {
            'jan': 0,
            'fev': 1,
            'mar': 2,
            'avr': 3,
            'mai': 4,
            'jun': 5,
            'jul': 6,
            'aou': 7,
            'sep': 8,
            'oct': 9,
            'nov': 10,
            'dec': 11,
        }
    }

    def _locale_keyword(self, lot):
        # Get month abbreviations in locale,
        # defaulting to English
        lang = self.message.reporter.language

        if lang in lot:
            return lot[lang]
        else:
            return lot['en']

    def _parse_period(self, keyword):

        keyword = keyword.lower()
        month_names = {}

        key_abbrs = self._locale_keyword(self.MONTHS)
        key_month = self._locale_keyword(self.MONTH)
        key_week = self._locale_keyword(self.WEEK)

        valid_periods = [key_week, key_month] + key_abbrs.keys()
        months = TwelveMonths.periods()[0].sub_periods()

        if keyword == key_month:
            # Use last month if it's the start of this month
            return months[10] if datetime.today().day < 10 else months[11]

        elif keyword == key_week:
            return LastSevenDays

        elif keyword in key_abbrs:
            # is 0 if user submitted "jan", 1 if "feb", ...
            index = key_abbrs[keyword]

            # is 1 if today is in January, 2, if in Feb, ...
            this_month = months[11].start.month

            shifted_index = (index - this_month) % 12
            return months[shifted_index]

        else:
            raise ValueError(_("Unknown period name: %(name)s. "\
                                "Valid periods are %(valid)s.") % \
                                {'name': keyword,
                                'valid': ', '.join(valid_periods)})


    @authenticated
    def process(self):
        chw = self.message.reporter.chw

        if len(self.params) == 1:
            # Default to last seven days
            period = LastSevenDays

        elif len(self.params) == 2:
            period = self._parse_period(self.params[1].lower())

        else:
            self.message.respond(_(u"Use ACTIVITY followed by WEEK, MONTH, or "\
                                    "the 3-letter month code."))
            return True
            
        patients = chw.patient_set.all()

        p = {}
        p['sdate'] = period.start.strftime('%d %b')
        p['edate'] = period.end.strftime('%d %b')
        p['severemuac'] = nutrition.Sam(period, patients)
        p['numhvisit'] = household.Total(period, patients)
        p['muac'] = nutrition.Mam(period, patients)
        p['rdt'] = fever.Total(period, patients)
        p['household'] = registration.Household(period, patients)
        p['tclient'] = registration.Total(period, patients)
        p['ufive'] = registration.UnderFive(period, patients)
        p['unine'] = registration.UnderNineMonths(period, patients)
        p['underone'] = registration.UnderOne(period, patients)

        self.message.respond(_(u"(%(sdate)s->%(edate)s): " \
                                "%(numhvisit)d household visit, %(muac)d " \
                                "MUAC (%(severemuac)d SAM/MAM) %(rdt)d RDT." \
                                " You have %(household)d households" \
                                ", %(ufive)d under 5y, %(underone)d under "\
                                "1y, %(unine)d under 9m, "\
                                "%(tclient)d total" \
                                " registered clients") % p)
