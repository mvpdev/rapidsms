#!/usr/bin/env python
# -*- coding= UTF-8 -*-

"""
    Set backends for all reporters in database
"""

import sys

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from childcount.models import Configuration


class Command(BaseCommand):

    help = u"View/Change CC+ configurations"

    def handle(self, *args, **options):
        if len(args):
            params = args
            command = params[0]
            if command == 'show':
                if params.__len__() > 1:
                    key = params[1]
                    try:
                        cfg = Configuration.objects.get(key__iexact=key)
                    except Configuration.DoesNotExist:
                        print u"Unknown config key: %s" % key
                    else:
                        print key, u":", cfg.value
                    return
                else:
                    for cfg in Configuration.objects.all():
                        print cfg.key, cfg.value
                    return
            elif command == 'set' and params.__len__() > 2:
                key = params[1]
                value = ' '.join(params[2:])
                obj, created = Configuration.objects.get_or_create(key=key)
                obj.value = value
                obj.save()
                print key, u":", value
                return
        print (u"------------------------------\n"
                "View/Change CC+ configurations\n"
                "------------------------------\n\n"
                "USAGE:\n------\n\trapidsms cc_config show [key]\n"
                "\trapidsms cc_config set key value\n")
