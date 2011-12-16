#!/usr/bin/python


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

###
### END - SETUP RAPIDSMS ENVIRONMENT
###


from reversion import revision
from childcount.models import Encounter
from datetime import datetime

revision.start()

i = 0
for encounter in Encounter.objects.all():
    i +=1
	encounter.sync_omrs__isnull = True
    encounter.sync_omrs = None
    encounter.save()

if i == 0:
	print "No encounters " 
else:
	print "%d Encounters have been reset to False " % i

revision.end()



