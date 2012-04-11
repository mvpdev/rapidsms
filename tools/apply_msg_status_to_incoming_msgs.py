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
# import manager now that the path is correct
from rapidsms import manager
from django.db import IntegrityError
from childcount.models import HealthId
###
### END - SETUP RAPIDSMS ENVIRONMENT
###

from logger_ng.models import LoggedMessage


print "MATCHED MESSAGES"
outgoing = LoggedMessage\
                        .objects\
                        .filter(direction=LoggedMessage.DIRECTION_OUTGOING)\
                        .exclude(response_to=None)\
                        .exclude(status='None')
c = 0
t = outgoing.count()
for msg in outgoing:
    incoming = msg.response_to
    incoming.status = msg.status
    incoming.save()
    c += 1
    if c % 1000 == 0:
        print "%d of %d (%s%%) done." % (c, t, int((round(c)/t)* 100))

print "%d of %d (%s%%) done." % (c, t, int((round(c)/t)* 100))

print "INFO"
msgs = LoggedMessage.objects.filter(text__startswith='Please make sure ')
t = msgs.count()
msgs.update(status=LoggedMessage.STATUS_INFO)
print "changed %d of %d records" % (t, msgs.count())
