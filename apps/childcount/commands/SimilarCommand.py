#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from reporters.models import Reporter
from childcount.models import HealthId

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated


class SimilarCommand(CCCommand):
    SIMILARITIES = {
        '1': ['1','L'],
        '2': ['2','Z','R'],
        '3': ['3','B','E','P'],
        '4': ['4','H','X','K'],
        '5': ['5','S'],
        '6': ['6','8','B'],
        '7': ['7','1'],
        '8': ['8','6','B'],
        '9': ['9'],
        '0': ['0'],
        'A': ['A','4',],
        'B': ['B','6','8'],
        'C': ['C','0'],
        'D': ['D','B'],
        'E': ['E','B','P'],
        'F': ['F','E','P'],
        'G': ['G','C','0'],
        'H': ['H','4','X','K'],
        'I': ['I','1','L'],
        'J': ['J'],
        'K': ['K','H'],
        'L': ['L','1','J'],
        'M': ['M','N'],
        'N': ['N','M','H'],
        'O': ['O','0'],
        'P': ['P','B'],
        'Q': ['Q','0'],
        'R': ['R','P','B'],
        'S': ['S','5'],
        'T': ['T'],
        'U': ['U','V'],
        'V': ['V','U'],
        'W': ['W'],
        'X': ['X','4','H'],
        'Y': ['Y','V','U'],
        'Z': ['Z','2'],
    }

    KEYWORDS = {
        'en': ['similar'],
        'rw': ['similar'],
        'fr': ['similar'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if len(self.params) != 2:
            self.message.respond(_(u"Similar command requires a single health ID"), \
                                   'error')
            return True
        
        possible_ids = self._similar_strings(list(self.params[1].upper()))
        patients = []
        health_ids = []
        for hid in possible_ids:
            try:
                p = Patient.objects.get(health_id=hid)
            except Patient.DoesNotExist:
                continue
            else:
                patients.append('%s - %s ' % \
                    (p.health_id.upper(), p.location.code))
                continue

            try:
                h = HealthId.objects.get(health_id=hid)
            except HealthId.DoesNotExist:
                continue
            else:
                health_ids.append(hid)

        if len(patients) == 0 and len(health_ids) == 0:
            self.message.respond(_(u"No similar health IDs found."))
            return True
        resp = u''

        if len(patients) > 0:
            resp += _(u"Patients: ") + ' | '.join(patients)
        if len(health_ids) > 0:
            resp += _(u"Unused IDs: ") + ' | '.join(health_ids)

        self.message.respond(resp, 'success')
        return True

    @classmethod
    def similar_strings(cls, inlst):
        out = []
        counts = [0] * len(inlst)
        max_counts = []
        for i,c in enumerate(counts):
            max_counts.append(len(cls.SIMILARITIES[inlst[i]]))

        index = 0
        while True:
            # Increment count
            if counts[index] == max_counts:


            #
            Make string according to count
            for i,v in enumerate(count):
            out.append(

            if index >= len(inlst):
                return out    

            c = inlst[index]

            if count >= len(cls.SIMILARITIES[c]):
                index += 1
                count = 0
                continue
            else:
                print (index, count)
                inlst[index] = cls.SIMILARITIES[c][count]
                out.append(''.join(inlst))
                count += 1
                continue

