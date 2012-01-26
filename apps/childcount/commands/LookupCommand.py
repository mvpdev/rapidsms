#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

from django.db.models import Q
from django.utils.translation import ugettext as _

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated


def remdup(seq):
    keys = {}
    for e in seq:
        keys[e] = 1
    return keys.keys()


class LookupCommand(CCCommand):
    ''' Responds HEALTH ID from names search

    Searches through first and last names of Patients
    Returns Name and Health ID 
    '''

    KEYWORDS = {
        'en': ['lookup'],
        'rw': ['lookup'],
        'fr': ['lookup'],
    }

    @authenticated
    def process(self):
        chw = self.message.reporter.chw

        # warn if no search terms
        if len(self.params) < 2:
            self.message.respond(_(u"Lookup command requires at least a " \
                                   "first or last name."), 'error')
            return True

        terms = self.params[1:]

        results = []
        if len(terms) == 1:
            results = chw\
                .patient_set\
                .filter(Q(first_name=terms[0])|Q(last_name=terms[0]))

        elif len(terms) == 2:
            # Match exctly on first and last names (also reversed)
            results = chw\
                .patient_set\
                .filter(
                    (Q(first_name=terms[0]) & Q(last_name=terms[1])) | \
                    (Q(first_name=terms[1]) & Q(last_name=terms[0])))

        else:
            results = chw\
                .patient_set\
                .filter(Q(first_name__in=terms)|Q(last_name__in=terms))

        # no results
        if not results:
            self.message.respond(_(u"No matching patient found. Please " \
                                   "retry with only first or last name."))
            return True

        # One results (best case)
        elif len(results) == 1:
            patient = results[0]
            self.message.respond(_(u"ID# %(name)s from " \
                                   "%(location)s") % { \
                                   'name': patient, \
                                   'location': patient.location})
            return True

        # multiple results
        names = [u"%(name)s/%(id)s/%(loc)s" % {'name': patient.full_name(), \
                                         'id': patient.health_id.upper(), \
                                         'loc': patient.location.code} \
                 for patient in results]

        # advise on quality of answers
        intro = _(u"%(total)s matches") % {'total': len(results)}

        # send list (max 10 patient)
        self.message.respond(
            _(u"%(intro)s: %(list)s") \
               % {'list': u", ".join(names[:10]), \
                  'intro': intro})

        return True
