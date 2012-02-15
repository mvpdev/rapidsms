#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Helper functions for use in App and U.I '''

import re
import datetime
import string
import random

from django.utils.translation import ugettext_lazy as _

from billboard.models import *


def to_seconds(period):
    ''' convert a mixed string into seconds

    return int.'''
    if period == 'hourly':
        return 3600
    elif period == 'daily':
        return 86400
    elif period == 'weekly':
        return 604800
    elif period == 'monthly':
        return 18144000
    elif period[0] == 's':
        return int(period[1:period.__len__()])
    elif period[0] == 'm':
        return int(period[1:period.__len__()]) * 60
    elif period[0] == 'h':
        return int(period[1:period.__len__()]) * 3600
    elif period[0] == 'd':
        return int(period[1:period.__len__()]) * 86400
    else:
        return 86400


def recipients_from(sender, target_str):
    ''' builds a list of recipients from sms string

    Examples: @ghana or @bonsaaso or @ghana,bonsaaso

    return array of Member '''
    targets = zonecodes_from_string(target_str.lower())
    recipients = zone_recipients(targets, sender)
    return recipients


class InsufficientCredit(Exception):
    ''' Member's credit not enough for action '''
    pass

config = Configuration.get_dictionary()


def price_fmt(price):
    ''' format price with currency

    return string '''
    return u"%(p)s%(c)s" % {'p': price, 'c': config['currency']}


def random_alias():
    ''' generate a random alias (10 chars)

    return string '''
    return "".join(random.sample(string.letters + string.digits, 10)).lower()


def zonecodes_from_string(zonestring):
    ''' builds a list of zones from SMS string '''
    zones = []
    zonesc = zonestring.split(',')
    for zone in zonesc:
        if zone.find('@') == 0:
            zone = zone.__getslice__(1, zone.__len__())
        if zones.count(zone) == 0:
            zones.append(zone)
    return zones


def zone_recipients(zonecode, exclude=None):
    ''' builds a list of recipients from a zone code '''
    if zonecode.__class__ == str:
        zonecode = [zonecode]

    recipients = []

    for zone in zonecode:
        try:
            query_zone = Zone.objects.get(name=zone)
            all_zones = recurs_zones(query_zone)
            all_boards = Member.objects.filter(active=True, \
                         membership=MemberType.objects.get(code='board'), \
                         zone__in=all_zones)
        except models.ObjectDoesNotExist:
            all_boards = Member.objects.filter(active=True, \
                         membership=MemberType.objects.get(code='board'), \
                         alias=zone)

        for board in all_boards.iterator():
            if recipients.count(board) == 0:
                recipients.append(board)

    if not exclude == None:
        try:
            recipients.remove(exclude)
        except:
            pass

    return recipients


def recurs_zones(zone):
    ''' loops on a zone to retrive children '''
    zonelist = []
    all_zones = Zone.objects.filter(zone=zone)
    for azone in all_zones.iterator():
        zonelist += recurs_zones(azone)
        zonelist.append(azone)
    zonelist.append(zone)
    return zonelist


def message_cost(sender, recipients, ad=None, fair=False):
    ''' calculate cost of a message

    sender: Member sending
    recipients: list of recipients
    ad: AdType of message
    fair: whether of not to use fair price
    return float '''
    price = 0
    if not ad == None:
        cost = ad.price
    else:
        mtype = sender.membership
        cost = mtype.fee

    for recip in recipients:
        if fair:
            price += float(config['fair_price'])
        else:
            price += (recip.rating * cost)

    return price


def ad_from(content):
    ''' return AdType from message text '''
    try:
        adt = re.search('^\s?\+([a-z])', content).groups()[0]
        adt = AdType.by_code(adt)
    except:
        adt = None
    return adt


def send_message(backend, sender, recipients, content, action=None, adt=None, \
                 overdraft=False, fair=False):
    ''' single step message sending

    - calculates cost of message
    - takes credit out of sender account
    - send message
    - log message '''
    plain_recip = recipients # save this for record_action
    if recipients.__class__ == str:
        recipients = Member(alias=random_alias(), rating=1, \
                            mobile=recipients, credit=0, \
                            membership=MemberType.objects.get(code='alien'))

    if recipients.__class__ == Member:
        recipients = [recipients]

    cost = message_cost(sender, recipients, adt, fair)
    if cost > sender.credit and not overdraft:
        raise InsufficientCredit

    mtype = sender.membership
    contrib = mtype.contrib

    content = _(u"%(alias)s> %(msg)s" % {'alias': sender.alias_display(), \
                                         'msg': content})[:160]

    for recipient in recipients:
        if recipient.is_board():
            recipient.credit += contrib
            recipient.save()

        msg = backend.message(recipient.mobile, content[:160])
        backend._router.outgoing(msg)

        log = MessageLog(sender=sender.mobile, sender_member=sender, \
                         recipient=recipient.mobile, \
                         recipient_member=recipient, text=content[:140], \
                         date=datetime.datetime.now())
        log.save()

    sender.credit -= cost

    if overdraft:
        if sender.credit < 0:
            sender.credit = 0

    sender.save()

    if action.__class__ == str and action != None:
        record_action(action, sender, plain_recip, content, cost, adt)

    return cost


def default_tag():
    ''' return default message tag from config '''
    if not config:
        config = Configuration.get_dictionary()

    return Tag.by_code(config['dfl_tag_code'])


def record_action(kind, source, target, text, cost, ad=None, \
                  date=datetime.datetime.now()):
    ''' log action in DB '''

    if target.__class__ == str:
        target = Member.system()

    if target.__class__ == Member:
        target = [target]

    action = Action(kind=ActionType.by_code(kind), source=source, text=text, \
                    date=date, cost=cost, ad=ad)
    action.save()

    for m in target:
        action.target.add(m)

    action.save()
    return action
