#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Billboard App Views

Index, Help, Zone List, History '''

import datetime

from rapidsms.config import Config
from django.db.models import Q
from django.template import Template, loader, Context
from django.http import HttpResponse
from django import forms
from django.contrib.admin.widgets import AdminTimeWidget.AdminDateWidget

from billboard.models import *
from billboard.utils import *


def month_start(date):
    ''' date of first day in month.

    return date '''
    return date.replace(day=1)


def month_end(date):
    ''' date of last day in month.

    return date '''
    for n in (31, 30, 28):
        try:
            return date.replace(day=n)
        except:
            pass
    return date


def day_start(date):
    ''' begining of day from date.

    return datetime '''
    t = date.time().replace(hour=0, minute=1)
    return datetime.datetime.combine(date.date(), t)


def day_end(date):
    ''' end of day from date.

    return datetime '''
    t = date.time().replace(hour=23, minute=59)
    return datetime.datetime.combine(date.date(), t)


def ovload_context(context):
    ''' add global config to templates via context '''
    co = {'conf': config}
    context.update(co)
    return context


def index(request):
    ''' display home page '''
    return HttpResponse(loader.get_template('body.html')\
                        .render(ovload_context(Context({'me': 'reg'}))))


def help(request):
    ''' display help page '''
    return HttpResponse(loader.get_template('help.html')\
                        .render(ovload_context(Context({}))))


def zone_list(request):
    ''' builds ordered list of zones and members from templates '''

    tree = []

    def zone_fill(tree, zone):
        dumb_board = Member(alias=random_alias(), rating=1, mobile='000000', \
                            credit=0, \
                            membership=MemberType.objects.get(code='board'))
        tlz = Zone.objects.filter(zone=zone)
        for z in tlz:
            recipients = zone_recipients(str(z.name))
            price = message_cost(dumb_board, recipients)
            zo = {'n': z.display_name(), 'p': price, 'pf': price_fmt(price)}
            zo['c'] = []
            zo['b'] = []
            bb = Member.objects.filter(zone=z, \
                             membership=MemberType.objects.get(code='board'), \
                             active=True)
            for board in bb:
                mc = message_cost(dumb_board, [board])
                bo = {'n': board.display_name(), 'c': board.rating, 'p': mc, \
                      'm': board.mobile, 'd': board.details, \
                      'pf': price_fmt(mc)}
                zo['b'].append(bo)
            zone_fill(zo['c'], z)
            tree.append(zo)

    zone_fill(tree, None)

    tb = loader.get_template('zone_list_block.html')

    def recurs_rend(templ, tree):
        op = ""
        for tr in tree:
            c = Context({'zone': tr})
            op += templ.render(c)
            op += recurs_rend(templ, tr['c'])
        return op

    tbh = recurs_rend(tb, tree)

    t = Template("{% extends 'body.html' %}{% block title %}List of Boards " \
                 "and Zones{% endblock %} {% block content %}" \
                 + tbh + "{% endblock %}")

    c = Context({
    })
    return HttpResponse(t.render(ovload_context(c)))


def history(request):
    ''' display history page: list of members to select from '''
    t = loader.get_template('history.html')
    c = Context({'members': Member.objects.all()})
    return HttpResponse(t.render(ovload_context(c)))


class DateForm(forms.Form):
    ''' Django Form helper '''
    date_from = forms.DateTimeField(widget=AdminDateWidget)
    date_to = forms.DateTimeField(widget=AdminDateWidget, required=False)


def history_one(request, alias):
    ''' display all action of a member '''
    now = datetime.datetime.now().replace(hour=23, minute=59)
    date_from = month_start(now)
    date_to = month_end(now)

    member = Member.objects.get(alias=alias)

    t = loader.get_template('history_one.html')

    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            date_from = day_start(form.cleaned_data['date_from'])
            if date_to:
                date_to = day_end(form.cleaned_data['date_to'])
    else:
        form = DateForm()

    actions = Action.objects.filter(Q(target=member) | Q(source=member), \
                                     Q(date__gte=date_from, date__lte=date_to))
    actions.query.group_by = ['billboard_action.id']

    total = 0
    for action in actions:
        if action.source == member:
            total += action.cost

    c = Context({'member': member,
                   'actions': actions,
                   'total': total,
                   'form': form})
    return HttpResponse(t.render(ovload_context(c)))


def database_backup(request):
    ''' generates a backup of sqlite database '''
    conf = Config("rapidsms.ini")
    f = open(conf['database']['name'], "r")
    h = HttpResponse(f)
    h._headers['content-type'] = ('Content-Type', 'application/octet-stream;')
    h._headers['content-disposition'] = ('Content-Disposition', \
                                        'attachment;filename="%s_%s"' \
                                        % (datetime.date.today()\
                                        .strftime("%Y-%m-%d"), \
                                        conf['database']['name']))
    return h
