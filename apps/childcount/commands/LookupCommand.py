#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

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
    Returns Name and Health ID '''

    KEYWORDS = {
        'en': ['lookup'],
        'fr': ['lookup'],
    }

    @authenticated
    def process(self):

        # warn if no search criteria
        if self.params.__len__() < 2:
            self.message.respond(_(u"Lookup command requires at least a " \
                                   "first or last name."), 'error')
            return True

        terms = self.params[1:]

        results = []

        exact = True

        for term in terms:
            # try first names
            patients = Patient.objects.filter(first_name__iexact=term)
            if patients.__len__() > 0:
                results.extend(patients)

            # try last names
            patients = Patient.objects.filter(last_name__iexact=term)
            if patients.__len__() > 0:
                results.extend(patients)

        if results.__len__() == 0:

            exact = False

            # retry with less restriction
            for term in terms:
                # try first names
                patients = Patient.objects.filter(first_name__icontains=term)
                if patients.__len__() > 0:
                    results.extend(patients)

                # try last names
                patients = Patient.objects.filter(last_name__icontains=term)
                if patients.__len__() > 0:
                    results.extend(patients)

        results = remdup(results)

        # no results
        if results.__len__() == 0:
            self.message.respond(_(u"No matching patient found. Please " \
                                   "retry with only first or last name."))
            return True

        # only one result (best case)
        if results.__len__() == 1:
            patient = results[0]
            self.message.respond(_(u"#%(id)s: %(name)s from " \
                                   "%(location)s") % { \
                                   'id': patient.health_id, \
                                   'name': patient.full_name(), \
                                   'location': patient.location})
            return True

        # multiple results
        names = [u"%(name)s/%(id)s" % {'name': patient.full_name(), \
                                         'id': patient.health_id} \
                 for patient in results]

        # advise on quality of answers
        if exact:
            intro = _(u"%(total)s matches") % {'total': results.__len__()}
        else:
            intro = _(u"%(total)s approx. matches") % {'total': \
                                                             results.__len__()}

        # send list (max 10 patient)
        self.message.respond(
            _(u"%(intro)s: %(list)s") \
               % {'list': u", ".join(names[:10]), \
                  'intro': intro})

        return True
