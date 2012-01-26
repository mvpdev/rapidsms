#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import django_tables as tables


class HealthUnitsTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    code = tables.Column(verbose_name=u"Code")
    name = tables.Column(verbose_name=u"Name")
    hctype = tables.Column(verbose_name=u"Type")
    hsd = tables.Column(verbose_name=u"HSD")
    reporters = tables.Column(verbose_name=u"Reporters")
    last = tables.Column(verbose_name=u"Last Report", sortable=False)
    last_pk = tables.Column(visible=False, sortable=False)
    last_sort = tables.Column(visible=False)
    last_color = tables.Column(sortable=False, visible=False)


class HWReportersTable(tables.Table):
    pk = tables.Column(visible=False, sortable=False)
    alias = tables.Column(verbose_name=u"Alias")
    name = tables.Column(verbose_name=u"Name")
    hu = tables.Column(verbose_name=u"Health Unit")
    hu_pk = tables.Column(visible=False, sortable=False)
    contact = tables.Column(verbose_name=u"Contact", sortable=False)
