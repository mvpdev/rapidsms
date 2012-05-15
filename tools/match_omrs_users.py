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
from mgvmrs.models import User

revision.start()

###
### Generate OpenMRS users from openmrs table like below
###
### select user_id, username 
### INTO OUTFILE '/tmp/users.csv' 
### FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
###   LINES TERMINATED BY '\n'
### FROM users;


with open('users.csv') as f:
    unknown = '';
    for line in f:
        d = line.strip().split(',')
        openmrs_id = d[0]
        username = d[1].replace('"','')
        try:
            user = User.objects.get(chw__username=username)
            user.openmrs_id = int(openmrs_id)
            user.save()
            print openmrs_id, username, user.chw, "\n"
        except User.DoesNotExist:
            try:
                chw = CHW.objects.filter(username=username.lower())
            except:
                unknown += username + ';'
            else:
                user = User()
                user.chw = chw
                user.openmrs_id = int(openmrs_id)
                user.save()
                print openmrs_id, username, user.chw, "CHW Link\n"
    print unknown
revision.end()

