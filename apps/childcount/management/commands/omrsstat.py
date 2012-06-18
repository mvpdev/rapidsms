#!/usr/bin/env python
# -*- coding= UTF-8 -*-

"""
    Show omrs sync statistics
"""

import sys

from optparse import make_option

from django.core.management.base import BaseCommand
from childcount.models import Encounter


class Command(BaseCommand):

    help = u'Show omrs sync statistics'

    def handle(self, *args, **options):
        allenc = Encounter.objects.all()

        print "All Encounters: ", allenc.count()
        print "OMRS Syncd: ", allenc.filter(sync_omrs=True).count()
        print "OMRS Not Syncd: ", allenc.filter().exclude(sync_omrs=True).count()
        print "OMRS Failed Sync: ", allenc.filter(sync_omrs=False).count()

        print "All HOH Encounters", allenc.filter(type='H').count()
        print "HOH OMRS Syncd: ", allenc.filter(type='H').filter(sync_omrs=True).count()
        print "HOH OMRS Not Syncd: ", allenc.filter(type='H').exclude(sync_omrs=True).count()
        print "HOH OMRS Failed Sync: ", allenc.filter(type='H').filter(sync_omrs=False).count()

        print "All Patient Encounters", allenc.filter(type='P').count()
        print "Patient OMRS Syncd: ", allenc.filter(type='P').filter(sync_omrs=True).count()
        print "Patient OMRS Not Syncd: ", allenc.filter(type='P').exclude(sync_omrs=True).count()
        print "Patient OMRS Failed Sync: ", allenc.filter(type='P').filter(sync_omrs=False).count()
