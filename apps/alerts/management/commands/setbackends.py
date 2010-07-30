#!/usr/bin/env python
# -*- coding= UTF-8 -*-

"""
    Set backends for all reporters in database
"""

import sys

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from reporters.models import PersistantBackend
from reporters.models import PersistantConnection
from reporters.models import Reporter


class Command(BaseCommand):

    BACKENDS = {
    'usbvbox': {'slug': 'usbvbox', 'title': 'usbvbox'},
    'http': {'slug': 'http_HttpHandler', 'title': 'http'},
    'ups': {'slug': 'ups', 'title': 'ups'},
    'pipe': {'slug': 'pipe', 'title': 'pipe'},
    'gsm': {'slug': 'pygsm', 'title': 'pyGSM'},
    'dataentry': {'slug': 'dataentry', 'title': 'dataentry'},
    'debackend': {'slug': 'debackend', 'title': 'debackend'}
    }


    help = u'Set a web backends for all reporters in database'

    option_list = BaseCommand.option_list + (
    
       make_option('--no-input',
            action='store_true',
            dest='no_input',
            default=False,
            help=u"Don't prompt user for any input. Delete without warnings."),
    
       make_option('--replace',
            action='store_true',
            dest='replace_backends',
            default=False,
            help=u"Replace original backends instead of adding one."),
    )
    

    def handle(self, *args, **options):
    
        replace_backends = options['replace_backends']
        no_input = options['no_input']
        create = 'y'
        confirm = 'y'
        added_count = 0
        deleted_count = 0

        if len(args) != 1:
            raise CommandError(u"Expecting one and only on argument")

        backend_type = args[0].strip().lower()
        
        try:
            backend_slug = Command.BACKENDS[backend_type]['slug']
            backend_title = Command.BACKENDS[backend_type]['title']
        except KeyError:
            backends = "', '".join(Command.BACKENDS.iterkeys())
            raise CommandError(u"'%s' backend is not available. Known "\
                               u"backends are: '%s'" % (backend_type, backends))

        found_backend = False
        for backend in settings.RAPIDSMS_CONF.data['rapidsms']['backends']:
            if backend['type'] == backend_type:
                found_backend = True
                break

        if not found_backend:
            raise CommandError(u"You must add the backend in "\
                               u"your .ini file first.")

        if not no_input:
            confirm = raw_input(u"This will change backends for all "\
                                u"reporters. Phone numbers may not be valid "\
                                u"anymore. Are you sure ? (y/N)\n")

            if not no_input and confirm.strip().lower() not in ('y', 'yes'):
                print "Aborting"
                sys.exit(1)

        print "Start"
        
        #pick backend
        
        try:
            backend = PersistantBackend.objects.get(slug=backend_slug)
        except PersistantBackend.DoesNotExist:

            if not no_input:    
                create = raw_input(u"The is no web backend in the data base."\
                                   u" Create one ?\n")
                
            if create in confirm.strip().lower() in ('y', 'yes'):
                pb = PersistantBackend(slug=backend_slug, title=backend_title)
                pb.save()
                print "Creating Backend"
            else:
                print "Aborting"
                sys.exit(0)

        # replace backends
        print 'Adding backend'
        c = 0
        reporters = Reporter.objects.all()
        for reporter in reporters:

            sys.stdout.write('.')
            if replace_backends:
                deleted_count += reporter.connections.all().count()
                reporter.connections.all().delete()
                
            while not reporter.connections.filter(backend__slug=backend_slug).count():
                try:
                    identity = str(reporter.id + c)
                    connection = PersistantConnection(backend=backend)
                    connection.identity = identity
                    connection.reporter = reporter
                    connection.save()
                    added_count += 1
                except:
                    c += 1
        print
        print '%s backends added' % added_count
        print '%s backends deleted' % deleted_count
       
