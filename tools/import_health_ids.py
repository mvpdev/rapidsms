#!/usr/bin/python

# create childcount clinic objects from locations that have clinic and hospital in their names

###
### START - SETUP RAPIDSMS ENVIRONMENT
###

import sys, os
from os import path

# figure out where all the extra libs (rapidsms and contribs) are
libs=[os.path.abspath('lib'),os.path.abspath('apps')] # main 'rapidsms/lib'
try:
    for f in os.listdir('contrib'):
        pkg = path.join('contrib',f)
        if path.isdir(pkg) and \
                'lib' in os.listdir(pkg):
            libs.append(path.abspath(path.join(pkg,'lib')))
except:
    pass

# add extra libs to the python sys path
sys.path.extend(libs)
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['RAPIDSMS_INI'] = os.path.join(path, "local.ini")
os.environ['DJANGO_SETTINGS_MODULE'] = 'rapidsms.webui.settings'
# import manager now that the path is correct
from rapidsms import manager
from django.db import IntegrityError
from childcount.models import HealthId
###
### END - SETUP RAPIDSMS ENVIRONMENT
###


from reversion import revision
from childcount.models import Clinic
from locations.models import Location

revision.start()

dups = 0 # number of duplicates
no_dups = 0 # number of non duplicates

with open('ids_full') as f:
    for line in f:
        line = line.strip()
        try:
            HealthId.objects.create(
                health_id = line,
                status = HealthId.STATUS_GENERATED)
            print "Adding health ID %s" % (line)
            no_dups += 1
        except IntegrityError:
            print "Skipping health ID %s" % (line)
            dups += 1
            
print "Added: %d; Failed: %d" % (no_dups, dups,)

revision.end()

