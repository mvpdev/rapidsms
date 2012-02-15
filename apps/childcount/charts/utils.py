#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import os

from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

CHARTS_DIR = 'charts'


def render_chart_to_response(request, binarydata, rformat='png',
        filebasename=_(u'chart')):
    filename = filebasename + '.' + rformat
    f = open(chart_filename(filename), 'w')
    f.write(binarydata)
    f.close()
    return HttpResponseRedirect( \
        '/static/childcount/' + CHARTS_DIR + '/' + filename)


def chart_filename(chart_name):
    return os.path.abspath(\
        os.path.join(
                    os.path.dirname(__file__), \
                    '..',
                    'static',
                    CHARTS_DIR,
                    chart_name))
