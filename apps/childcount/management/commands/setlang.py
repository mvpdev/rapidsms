#!/usr/bin/env python
# -*- coding= UTF-8 -*-

"""
    Set backends for all reporters in database
"""

import sys

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from reporters.models import Reporter


class Command(BaseCommand):

    help = u'Set same language for all reporters'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError(u"Expecting one and only on argument")

        language = args[0].strip().lower()
        
        Reporter.objects.update(language=language)
