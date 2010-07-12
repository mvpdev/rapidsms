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


from childcount.reports import *

reports_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), \
                                        '../apps/childcount/rpts'))
#check if reports folder is there
if not os.path.isdir(reports_folder):
    os.mkdir(reports_folder)
filename = os.path.join(reports_folder, 'operationalreport.pdf')

story = []
buffer = StringIO()

#Sauri's CHWs were location was clinic, some locations would draw blank reports
if Clinic.objects.all().count():
    locations = Clinic.objects.all()
else:
    locations = Location.objects.all()
for location in locations:
    if not TheCHWReport.objects.filter(location=location).count():
        continue
    tb = operationalreportable(location, TheCHWReport.objects.\
        filter(location=location))
    story.append(tb)
    story.append(PageBreak())

doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), \
                        topMargin=(0 * inch), \
                        bottomMargin=(0 * inch))
doc.build(story)

# Get the value of the StringIO buffer and write it to the response.
pdf = buffer.getvalue()
buffer.close()
f = open(filename, 'w')
f.write(pdf)
f.close()
