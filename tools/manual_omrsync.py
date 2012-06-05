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
import logging

from mgvmrs.encounters import send_to_omrs

logger = logging.getLogger('manual_omrs_sync')
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler("manual_omrs_sync.log")
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

class DLOG():
    def log(self, level, msg):
        level = getattr(logging, level.upper())
        logger.log(level, msg)

if __name__ == "__main__":
    num_encounters = 200
    if sys.argv.__len__() > 1:
        params = sys.argv[1:]
        num_encounters = int(params[0])
    log = DLOG()
    log.log('debug', "STARTING MANUAL OMRS SYNC")
    send_to_omrs(log, num_encounters=num_encounters)
