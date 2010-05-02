#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

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
    pass

# add extra libs to the python sys path
sys.path.extend(libs)
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['RAPIDSMS_INI'] = os.path.join(path, "local.ini")
os.environ['DJANGO_SETTINGS_MODULE'] = 'rapidsms.webui.settings'


#### BEGIN SCRIPT


from django.contrib.auth.models import Group, Permission


'''
    (name_of_auth_group,
        (permission codenames)
    )

'''

permissions_list = [
    ('dtu lab tech',
        ('add_specimen', 'send_specimen')
    ),
    ('ntrl lab tech',
        ('change_specimen', 'receive_specimen')
    ),
]

for item in permissions_list:
    group_name = item[0]
    permissions_tuple = item[1]
    group = Group.objects.get(name__iexact=group_name)
    group.permissions.clear()
    for permission_code in permissions_tuple:
        permission = Permission.objects.get(codename__iexact=permission_code)
        group.permissions.add(permission)
    group.save()
