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
###
### END - SETUP RAPIDSMS ENVIRONMENT
###


from reversion import revision
from childcount.models import Clinic
from locations.models import Location

revision.start()

#the name contains clinic
locations = Location.objects.filter(name__icontains='clinic')
for location in locations:
    clinic = Clinic(location_ptr=location)
    clinic.save_base(raw=True)

#the name contains hospital
locations = Location.objects.filter(name__icontains='hospital')
for location in locations:
    clinic = Clinic(location_ptr=location)
    clinic.save_base(raw=True)

revision.end()

