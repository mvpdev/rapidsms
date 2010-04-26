#!/usr/bin/env python
# -*- coding= UTF-8 -*-
#!/usr/bin/python

import sys, os
from os import path

# figure out where all the extra libs (rapidsms and contribs) are
libs=[os.path.abspath('lib'), os.path.abspath('apps')] # main 'rapidsms/lib'
try:
    for f in os.listdir('contrib'):
        pkg = path.join('contrib',f)
        if path.isdir(pkg) and \
                'lib' in os.listdir(pkg):
            libs.append(path.abspath(path.join(pkg,'lib')))
except:
    # could be several reasons:
    # no 'contrib' dir, 'contrib' not a dir
    # 'contrib' not readable, in any case
    # ignore and leave 'libs' as just
    # 'rapidsms/lib'
    pass

# add extra libs to the python sys path
sys.path.extend(libs)
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['RAPIDSMS_INI'] = os.path.join(path, "local.ini")
os.environ['DJANGO_SETTINGS_MODULE'] = 'rapidsms.webui.settings'
# import manager now that the path is correct

import csv, pprint

f = open("2008_Uganda_districts.csv")
c = csv.reader(f)

places = {}
for row in c :
    if not len(row[1].strip()):
        break
    districts = places.setdefault(row[0], {})
    dtus = districts.setdefault(row[1], [])
    dtus.append(row[2])

from locations.models import Location, LocationType
import string
import unicodedata


def make_code(str, remove=u'AEIOUY '):
    u_str = str.decode("utf8")
    norm_str = unicodedata.normalize(u'NFKD', u_str).encode(u'ascii', 
                                                            u'ignore')
    clean_str = norm_str.decode('ascii').strip().upper()
    
    translate_table = dict(((ord(letter), None) for letter in remove))
    return clean_str.translate(translate_table)


types = [u"zone", u"district", u"dtu"]
for type in types:
    location = LocationType.objects.get_or_create(name=type)[0].save()
    
for z, districts in places.iteritems():
    loc = LocationType.objects.get(name=u"zone")
    code = make_code(z)
    print code
    zone = Location.objects.get_or_create(type=loc, name=z.strip(), 
                                          code=code)[0]
    zone.save()
    
    for d, dtus in districts.iteritems():
        loc = LocationType.objects.get(name="district")
        code = make_code(d)
        print "\t", code
        try:
            district = Location.objects.get_or_create(type=loc, name=d.strip(),
                                                    code=code, parent=zone)[0]
        except :
            code = make_code(z) + code     
            district = Location.objects.get_or_create(type=loc, name=d.strip(),
                                                    code=code, parent=zone)[0]
        
            district.save()
        
        for u in dtus:
            loc = LocationType.objects.get(name="dtu")
            code = make_code(u)
            print "\t\t", code
            
            try:
                dtu = Location.objects.get_or_create(type=loc, 
                                                     name=u.strip(),
                                                     code=code, 
                                                     parent=district)[0]                
            except :
                code = make_code(d) + code     
                dtu = Location.objects.get_or_create(type=loc, 
                                                     name=u.strip(),
                                                     code=code, 
                                                     parent=district)[0]                           
            
            dtu.save()
        
