#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

import httplib
import urllib
from datetime import datetime

from childcount.models import Configuration

from mgvmrs.forms.OpenMRSFormInterface import *

try:
    openmrs_config = {
        'path_xform_post': Configuration.get('openmrs_path_xform_post'),
        'password': Configuration.get('openmrs_password'),
        'user': Configuration.get('openmrs_user'),
        'server_port': Configuration.get('openmrs_server_port'),
        'server': Configuration.get('openmrs_server'),
    }
except Configuration.DoesNotExist:
    raise
    openmrs_config = {
        'path_xform_post': "/openmrs/module/xforms/xformDataUpload" \
                                   ".form?uname=%(username)s&pw=%(password)s",
        'password': "pass",
        'user': "admin",
        'server_port': "8080",
        'server': "192.168.5.202",
    }

try:
    openmrs_config['store_xforms'] = \
                                bool(Configuration.get('openmrs_store_xforms'))
    openmrs_config['path_store_xforms'] = \
                                 Configuration.get('openmrs_path_store_xforms')
except Configuration.DoesNotExist:
    openmrs_config['store_xforms'] = False
    openmrs_config['path_store_xforms'] = u"/tmp"


def transmit_form(form):
    ''' send a Form to the OpenMRS system

    raise OpenMRSTransmissionError on error '''

    #print "sending to %s" % openmrs_config['server']
    xml_form = form.render()

    # print sent XML for debug
    #print xml_form

    headers = {"Content-type": "text/xml", "Accept": "text/plain"}

    try:
        conn = httplib.HTTPConnection("%(server)s:%(port)s" \
                                  % {'server': openmrs_config['server'], \
                                     'port': openmrs_config['server_port']})
    # TODO: identify appropriate exceptions
    except:
        raise OpenMRSTransmissionError("Unable to connect to server.")

    try:
        conn.request("POST", openmrs_config['path_xform_post'] \
                        % {'username': openmrs_config['user'], \
                           'password': openmrs_config['password']}, \
                        xml_form, headers)
    except:
        raise OpenMRSTransmissionError("Unable to query URI path.")

    response = conn.getresponse()
    # we assume only 200 is ok
    if response.status != 200:
        raise OpenMRSTransmissionError("%(code)s. %(reason)s" \
                                       % {'code': response.status, \
                                          'reason': response.reason})
    # data is useless right now
    data = response.read()
    conn.close()

    # we assume data went to OMRS now ; we shoult thus record the file.
    if openmrs_config['store_xforms']:
        f = open("%(path)s/omrs_%(date)s.xform" % {\
                                 'path': openmrs_config['path_store_xforms'], \
                                 'date': datetime.now().strftime("%s")}, 'w')
        f.write(xml_form)
        f.close()
    #print data
