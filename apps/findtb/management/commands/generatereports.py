#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from django.core.management.base import BaseCommand, CommandError

from findtb.libs.utils import create_tsrs_xls


"""
    Starts EQA for the current quarter for the given DTU(s) 
"""

class Command(BaseCommand):


    args = ''
    help = u'Generates monthly reports'

    def handle(self, *args, **options):
        create_tsrs_xls()
