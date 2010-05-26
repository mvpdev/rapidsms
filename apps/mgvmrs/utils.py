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
    #print data
