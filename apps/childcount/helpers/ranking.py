#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""Helper functions for ranking CHWs in
relation to each other.

"""

import random
from datetime import datetime, timedelta

from reporters.models import Reporter

from childcount.models import CHW

from childcount.indicators import household

from django.utils.translation import ugettext as _
from django.db.models.aggregates import Count

PHRASES = (
    (_("Congratulations!"), _("Excellent!"), _("Yebale!")),
    (_("Nice work."), _("Well done!")), 
    (_("Thank you for your very hard work."),),
    (_("Thank you for your very hard work."),),
    (_("Thank you for your good work."),),
    (_("Thank you for your good work."),),
    (_("Thank you for your work."),),
    (_("Thank you for your work."),),
    (_("Thank you for your work."),),
)

class PastThirtyDays(object):
    end = datetime.now()
    start = datetime.now() - timedelta(30)

def rank_message(ind, all_rankings, rank):
    """
    Return a message for the person who is ranked "rank" (zero-indexed).

    :param ind: Indicator 
    :param all_rankings: The list of dicts describing the 
                         rankings for all CHWs
    :param rank: Zero-indexed integer indicating rank
    """
   
    msg = all_rankings[rank]['chw'].first_name + u": "
    if rank < len(PHRASES):
        msg += random.choice(PHRASES[rank]) + u" "

    msg += _("You have ranked #%(rank)d out of %(total)d "\
            "active CHWs for the indicator \"%(ind_name)s\" "\
            "in the past 30 days. You achieved a value of "\
            "%(value)s.") %  {
                'rank': rank+1,
                'total': len(all_rankings),
                'ind_name': ind.short_name,
                'value': all_rankings[rank]['value'],
            }

    if rank > 0:
        msg += _(" Top performer was %(top)s with %(max)s.") % {
            'max': all_rankings[0]['value'],
            'top': all_rankings[0]['chw'].full_name(),
        }

    return msg

def compute_rankings(ind):
    """
    Return a list of dictionaries (one per CHW)
    for an indicator, where CHWs are ranked
    in decreasing order -- from highest
    indicator value to lowest.
    Each dict has values for the 'chw' and a 'value' keys.

    :param ind: Indicator on which to rank
    :type ind: :class:`indicator.indicator.Indicator`

    :return: :class:`list`
    """
    if not ind.output_is_number():
        raise ValueError("Indicator must output a number")

    if not ind.input_is_query_set():
        raise ValueError("Indicator must output a number")
      

    perc = ind.output_is_percentage()
    output = []

    # Iterate over CHWs who have patients
    for chw in CHW.objects.annotate(c=Count('patient')).filter(c__gt=0):
   
        qset = chw.patient_set.all()
        if ind.type_in.mtype.__name__ == "Reporter":
            qset = Reporter.objects.filter(pk=chw.pk)

        value = ind(PastThirtyDays, qset)

        # Don't include percentages of 0/0
        if perc and value.den == 0: 
            continue

        output.append({
            'chw': chw, 
            'value': value,
        })

    output.sort(key=lambda x: -x['value'])
    return output


