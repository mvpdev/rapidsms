#!/usr/bin/python

# update openmrs_id with openmrs info

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
###
### END - SETUP RAPIDSMS ENVIRONMENT
###


from reversion import revision
from childcount.models import Encounter

# reset omrs_sync=False to None for resending to omrs
encounters = Encounter.objects.filter(sync_omrs=False)
c = 0
t = encounters.count()
for e in encounters:
    c += 1
    revision.start()
    e.sync_omrs = None
    e.save()
    revision.end()
    if c % 100 == 0:
        print "DONE: ", c, "of", t, "%d%%" % round((round(c)/t)*100)
if c > 0:
    print "FINISHED: ", c, "of", t, "%d%%" % round((round(c)/t)*100)
else:
    print "FINISHED: ", c, "of", t
