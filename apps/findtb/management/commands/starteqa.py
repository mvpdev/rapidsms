#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from locations.models import Location

from findtb.models import SlidesBatch, EqaStarts

from django_tracking.models import TrackedItem

"""
    Starts EQA for the current quarter for the given DTU(s) 
"""

class Command(BaseCommand):


    args = '<dtu_id dtu_id ...>'
    help = u'Starts EQA for the current quarter for the given DTU(s)'

    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help=u'Start EQA for all DTU registered in the database'),
    )

    def handle(self, *args, **options):
        
        dtus = set()
        not_dtu_codes = set()
        not_location_codes = set()
        
        # checking input sanity
        if options['all']:
            if args:
                raise CommandError('The --all option should be use without any other arguments' )
            else:
                dtus = Location.objects.filter(type__name="dtu")
                
        else:
            if not args:
                raise CommandError('You must provide DTU codes' )
            else:
                for dtu_id in args:
                    try:
                        dtu = Location.objects.get(code=dtu_id)
                    except Location.DoesNotExist:
                        not_location_codes.add(dtu_id)
                    else:
                        if dtu.type.name != 'dtu':
                            not_dtu_codes.add((dtu_id,  
                                               dtu.name, 
                                               dtu.type.name))
                        else:
                            dtus.add(dtu)
         
        if not_location_codes:
            codes = ", ".join(not_location_codes)
            raise CommandError('These codes are not valid location codes: %s' % codes)            
                        
        if not_dtu_codes:
            codes = ", ".join("%s (%s is a %s)" % _id for _id in not_dtu_codes)
            raise CommandError('These codes are not DTU codes: %s' % codes )
        
        started = []
        not_started = []
        
        print "Starting EQA..."
        
        # starting EQA 
        for dtu in dtus:
            
            try:
                sb = SlidesBatch(location=dtu)
                sb.save()
            except IntegrityError:
                not_started.append(dtu)
            else:
                print "For [%s] %s" % (dtu.code, dtu.name) 
                started.append(dtu)
                state = EqaStarts(slides_batch=sb)
                state.save()
                TrackedItem.add_state_to_item(sb, state)
                
        print "EQA started in %s DTU(s)" % len(started)
        print "Skiped %s DTU(s) that already started it" % len(not_started)


