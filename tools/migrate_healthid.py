#!/usr/bin/python

# Migrate unused HealthIDS to CHWHealthId table

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
from childcount.models import HealthId, CHWHealthId
###
### END - SETUP RAPIDSMS ENVIRONMENT
###


from reversion import revision

revision.start()

hh = HealthId.objects.filter(status= HealthId.STATUS_GENERATED)

for x in hh:
    try:
        CHWHealthId.objects.create(health_id=x)
    except:
        print "Skipping health ID %s" % x.health_id

revision.end()

