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

from childcount.models import Configuration


def usage():
    print ("USAGE:\n\tpython tools/cc_configuration.py show [key]\n"
            "\tpython tools/cc_configuration.py set key value\n")


if __name__ == "__main__":
    if sys.argv.__len__() > 1:
        params = sys.argv[1:]
        command = params[0]
        if command == 'show':
            if params.__len__() > 1:
                key = params[1]
                try:
                    cfg = Configuration.objects.get(key__iexact=key)
                except Configuration.DoesNotExist:
                    print "Unknown config key: %s" % key
                else:
                    print key, ":", cfg.value
            else:
                for cfg in Configuration.objects.all():
                    print cfg.key, cfg.value
        elif command == 'set' and params.__len__() > 2:
            key = params[1]
            value = ' '.join(params[2:])
            obj, created = Configuration.objects.get_or_create(key=key)
            obj.value = value
            obj.save()
            print key, ":", value
        else:
            usage()
    else:
        usage()
