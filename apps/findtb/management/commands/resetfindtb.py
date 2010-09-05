#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from optparse import make_option
import os
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata
from django.conf import settings
from django.contrib.auth.models import Group

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
        
        # filtering all non app related reporter prior to deletion
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
            
            try:
                role.group.delete()
            except Group.DoesNotExist:
                pass # no group
            
            try:
                if role.reporter not in reporters_to_keep:
                    role.reporter.delete()
            except Reporter.DoesNotExist:
                pass # no reporter
                
            try:
                if role.location not in locations_to_keep:
                    role.location.delete()
            except Location.DoesNotExist:
                pass # no location
                
            try:
                role.delete()
            except (Group.DoesNotExist, Reporter.DoesNotExist, 
                   Location.DoesNotExist), e:
                pass # no group
            
            
        FINDTBGroup.objects.filter(name__in= groups_to_remove).delete()
        
        print "Deleting states"
        for state in State.objects.filter(origin=app):
            try:
                ti = state.tracked_item
                co = ti.content_object
                try:
                    reporter = co.reporter
                    if reporter not in reporters_to_keep:
                        reporter.delete()
                except AttributeError:
                    pass # no reporter
            except django_tracking.models.DoesNotExist:
                pass # no tracked item
            state.delete()
            ti.delete()
            
    

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
                    sys.exit(1)
            
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
        
            if not no_input:
                confirm = raw_input(u"This will wipe all current data for sref, "\
                      u"and sref related entries in django_tracking, group, "\
                      u"location and reporter then "\
                      u"reload sref fixtures. Are you sure ? (y/N)\n")

                if not no_input and confirm.strip().lower() not in ('y', 'yes'):
                    print "Aborting"
                    sys.exit(1)
        
            sref_only_groups = (FINDTBGroup.DTU_LAB_TECH_GROUP_NAME,
                                FINDTBGroup.CLINICIAN_GROUP_NAME)
        
            self.delete_states_and_roles('sref', sref_only_groups)
            
            print "Deleting specimens"
            Specimen.objects.all().delete()
            print "Deleting patients"
            Patient.objects.all().delete()

        if app == "eqa":
        
            if not no_input:
                confirm = raw_input(u"This will wipe all current data for eqa, "\
                      u"and eqa related entries in django_tracking, group, "\
                      u"location and reporter then "\
                      u"reload eqa fixtures. Are you sure ? (y/N)\n")

                if not no_input and confirm.strip().lower() not in ('y', 'yes'):
                    print "Aborting"
                    return
        
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
