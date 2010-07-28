#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from optparse import make_option
import os

from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata
from django.conf import settings

from locations.models import Location

from reporters.models import Reporter

from findtb.models import *

from django_tracking.models import *

FIXTURE_DIR = os.path.join(settings.PROJECT_ROOT, 'fixtures')


"""
    Reset FindTb and reload fixtures.
"""

class Command(BaseCommand):

    args = "<sref|eqa|stock|all>"
    help = u'Reset DB for FindTB and all dependancies and load fixtures.'

    option_list = BaseCommand.option_list + (
        make_option('--no-input',
            action='store_true',
            dest='no_input',
            default=False,
            help=u"Don't prompt user for any input. Delete without warnings."),
            
       make_option('--load-tests',
            action='store_true',
            dest='load_tests',
            default=False,
            help=u"Load test fixtures."),
    )
    
    
    def loaddata(self, load_tests=False, files=()):
        """
        Load fixtures of findtb using the manage.py command line.
        """
    
        if not files:
            fixtures = ('locations', 'groups', 'configurations')
            files = [os.path.join(FIXTURE_DIR, f + '.json') for f in fixtures]  
            if load_tests:
                files.append(os.path.join(FIXTURE_DIR, 'tests.json'))     
        
        cmd = loaddata.Command()
        cmd.handle(*files)
        
    
    def delete_states_and_roles(self, app, groups_to_remove=()):
        """
        Delete states, roles and associated locations/groups/reporters
        for the given app.
        """
        
        # filtering all non sref related reporter prior to deletion
        reporters_to_keep = set((None,))
        locations_to_keep = set((None,))
        for state in State.objects.exclude(origin=app):
            item = state.tracked_item.content_object
            location = item.created_by
            reporter = item.created_by
            if reporter:
                reporters_to_keep.add(reporter)
            if location:
                locations_to_keep.add(location)
                
        # deleting roles and filtering non sref related groups/locations prior to deletion
        print "Deleting roles, reporter, groups and locations"
        for role in Role.objects.filter(group__name__in= groups_to_remove):
            
            role.group.delete()
            
            if role.reporter not in reporters_to_keep:
                role.reporter.delete()
            if role.location not in locations_to_keep:
                role.location.delete()
                
            role.delete()
            
        FINDTBGroup.objects.filter(name__in= groups_to_remove).delete()
        
        print "Deleting states"
        for state in State.objects.filter(origin=app):
            ti = state.tracked_item
            co = ti.content_object
            reporter = co.reporter
            state.delete()
            ti.delete()
            if reporter not in reporters_to_keep:
                reporter.delete()
    

    def handle(self, *args, **options):
    
        if len(args) != 1:
            raise CommandError(u"Expecting one and only one argument")
            
        app = args[0].strip().lower()
        no_input = options['no_input']
        load_tests = options['load_tests']
        
        if app not in ('sref', 'eqa', 'stock', 'all'):
            raise CommandError(u"Accept only: 'sref', 'eqa', 'all'")
        
        if app == 'all':
        
            if not no_input:
                confirm = raw_input(u"This will wipe all current data for findtb, "\
                      u"django_tracking, group, location and reporter then "\
                      u"reload findtb fixtures. Are you sure ? (y/N)\n")

                if not no_input and confirm.strip().lower() not in ('y', 'yes'):
                    print "Aborting"
                    return
            
            print "Deleting states"
            Sref.objects.all().delete()
            TrackedItem.objects.all().delete()
            State.objects.all().delete()
            print "Deleting slides"
            SlidesBatch.objects.all().delete()
            Slide.objects.all().delete()
            print "Deleting specimens"
            Specimen.objects.all().delete()
            print "Deleting patients"
            Patient.objects.all().delete()
            print "Deleting roles and groups"
            FINDTBGroup.objects.all().delete()
            print "Deleting locations"
            Location.objects.all().delete()
            print "Deleting reporters"
            Reporter.objects.all().delete()
            print "Deleting configuration"
            Configuration.objects.all().delete()
            print "Deleting notices"
            Notice.objects.all().delete()
            
        if app == "sref":
        
            sref_only_groups = (FINDTBGroup.DTU_LAB_TECH_GROUP_NAME,
                                FINDTBGroup.CLINICIAN_GROUP_NAME)
        
            self.delete_states_and_roles('sref', sref_only_groups)
            
            print "Deleting specimens"
            Specimen.objects.all().delete()
            print "Deleting patients"
            Patient.objects.all().delete()

        if app == "eqa":
            sref_only_groups = (FINDTBGroup.DTU_FOCAL_PERSON_GROUP_NAME,
                                FINDTBGroup.FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME,
                                FINDTBGroup.SECOND_CONTROL_FOCAL_PERSON_GROUP_NAME)
        
            self.delete_states_and_roles('eqa', sref_only_groups)
            
            print "Deleting slides"
            Slide.objects.all().delete()
            SlidesBatch.objects.all().delete()

        if app == "notice":
            raise CommandError("Not implemented")
            
        self.loaddata(load_tests=load_tests)
