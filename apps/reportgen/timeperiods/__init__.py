from django.utils.translation import ugettext as _

from reportgen.timeperiods.PeriodType import PeriodType
from reportgen.timeperiods.Period import Period
from reportgen.timeperiods.SubPeriod import SubPeriod

from reportgen.timeperiods.definitions.FourWeeks import FourWeeks
from reportgen.timeperiods.definitions.ThirteenWeeks import ThirteenWeeks
from reportgen.timeperiods.definitions.Month import Month
from reportgen.timeperiods.definitions.TwelveMonths import TwelveMonths
from reportgen.timeperiods.definitions.TwoMonths import TwoMonths
from reportgen.timeperiods.definitions.FiveYears import FiveYears
from reportgen.timeperiods.definitions.SevenYearsByQuarter import SevenYearsByQuarter
from reportgen.timeperiods.definitions.ThreeYearsByQuarter import ThreeYearsByQuarter
from reportgen.timeperiods.definitions.MonthByDays import MonthByDays
from reportgen.timeperiods.definitions.TwelveMonthsByQuarter \
    import TwelveMonthsByQuarter
from reportgen.timeperiods.definitions.SixMonths import SixMonths
from reportgen.timeperiods.definitions.QuarterByMonth import QuarterByMonth

PERIOD_TYPES = [FourWeeks, Month, TwelveMonths,ThirteenWeeks, QuarterByMonth, \
                TwelveMonthsByQuarter, TwoMonths, SixMonths, FiveYears, \
                SevenYearsByQuarter, ThreeYearsByQuarter, MonthByDays]

PERIOD_CHOICES = [(pt.code, "%s (0-%d)" % (pt.title, pt.n_periods-1)) \
                            for pt in PERIOD_TYPES]


def period_type_for(code):
    for pt in PERIOD_TYPES:
        if pt.code == code: return pt
    raise RuntimeError(_("No period type with code %s")%code)
