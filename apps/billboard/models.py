#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Billboard App Models

Zone - location
MemberType - Text log of prepaid messages
Member - Action log of prepaid sessions
ActionType - supported actions
Action - logical log
AdType - wedding, etc
MessageLog - textual log
BulkMessage - holder for messages sent outside of App (scheduler)
Configuration '''

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


def a_join(ar):
    ''' joins items of an array with colons '''
    s = ""
    for a in ar:
        s += u"%s, " % a
    return s[0:s.__len__() - 2]


class Zone(models.Model):

    ''' recursive geopgraphical area '''

    name = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=50, blank=True, null=True)
    zone = models.ForeignKey('Zone', verbose_name=_("Parent Zone"), \
                             blank=True, null=True, \
                             related_name="related_zone")

    def __unicode__(self):
        return u"%s (@%s)" % (self.full_name, self.name) \
               if not self.full_name == None else self.name

    def display_name(self):
        return self.__unicode__()

    @classmethod
    def by_name(cls, name):
        ''' get Zone by name or None '''
        try:
            return cls.objects.get(name=name)
        except models.ObjectDoesNotExist:
            return None


class MemberType(models.Model):

    ''' Type of Member (charges vary) '''

    name = models.CharField(max_length=20)
    code = models.CharField(max_length=10)
    fee = models.FloatField()
    contrib = models.FloatField(_(u'Contribution'))

    def __unicode__(self):
        return self.name

    @classmethod
    def by_code(cls, code):
        ''' get MemberType by code or None '''
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            return None


class Member(models.Model):

    ''' Member and datas related '''

    class Meta:
        app_label = "billboard"
    user = models.OneToOneField(User)
    alias = models.CharField(_("Alias"), max_length=10, \
                             unique=True, db_index=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=16, db_index=True, unique=True)
    membership = models.ForeignKey(MemberType, verbose_name=_(u'Type'))
    active = models.BooleanField(default=True)
    credit = models.FloatField(default=0)
    rating = models.IntegerField(_("Rating"), default=1)
    zone = models.ForeignKey(Zone)
    latitude = models.CharField(_('Latitude'), max_length=25, \
                                blank=True, null=True)
    longitude = models.CharField(_('Longitude'), max_length=25, \
                                 blank=True, null=True)
    picture = models.ImageField(_('Picture'), upload_to='board_pics', \
                                blank=True, null=True)
    details = models.TextField(blank=True)

    def __unicode__(self):
        return self.display_name()

    def display_name(self):
        ''' name formatting '''
        if self.name != None:
            front = self.name
        else:
            if self.user.first_name or self.user.last_name:
                front = "%s %s" % (self.user.first_name, self.user.last_name)
            else:
                return self.alias
        return u'%(front)s (@%(alias)s)' \
               % {'front': front, 'alias': self.alias}

    def is_board(self):
        ''' Member is of MemberType 'board' '''
        return bool(self.membership == MemberType.objects.get(code='board'))

    def is_admin(self):
        ''' Member is of MemberType 'admin' '''
        return bool(self.membership == MemberType.objects.get(code='admin'))

    def alias_zone(self):
        ''' displays Member' alias and zone '''
        return u"@%(alias)s (@%(zone)s)" \
               % {'alias': self.alias, 'zone': self.zone.name}

    def alias_display(self):
        ''' displays alias '''
        return u"@%(alias)s" % {'alias': self.alias}

    def status(self):
        ''' string status of Member '''
        if self.active:
            return _(u"Active")
        else:
            return _(u"Inactive")

    @classmethod
    def by_mobile(cls, mobile):
        ''' get Member by mobile number or None '''
        try:
            return cls.objects.get(mobile=mobile, active=True)
        except models.ObjectDoesNotExist:
            return None

    @classmethod
    def system(cls):
        ''' get system user (alias=sys) '''
        return cls.objects.get(alias='sys')

    @classmethod
    def active_boards(cls):
        ''' get alll active Member '''
        ba = []
        ab = cls.objects.filter(\
                             membership=MemberType.objects.get(code='board'), \
                             active=True)
        for b in ab:
            ba.append(b)
        return ba


class ActionType(models.Model):

    ''' Type of Billboard Action '''

    code = models.CharField(max_length=25, primary_key=True)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    @classmethod
    def by_code(cls, code):
        ''' get ActionType by code or None '''
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            return None


class Action(models.Model):

    ''' Log of Billboard Actions '''

    kind = models.ForeignKey("ActionType", \
                             related_name="%(class)s_related_kind")
    source = models.ForeignKey("Member", \
                               related_name="%(class)s_related_source")
    target = models.ManyToManyField("Member", \
                                    related_name="%(class)s_related_target", \
                                    blank=True)
    text = models.CharField(max_length=1400)
    date = models.DateTimeField()
    cost = models.FloatField(default=0)
    ad = models.ForeignKey("AdType", null=True, blank=True, \
                           related_name="%(class)s_related_ad")

    def __unicode__(self):
        return u"%(from)s %(kind)s (%(cost)s)" % {'from': self.source.alias, \
               'kind': self.kind, 'cost': self.cost}

    def targets(self):
        ''' displays wrapped list of action targets (recipients) '''
        if self.target.count() == 0:
            return "None"
        elif self.target.count() > 0:
            tt = []
            for t in self.target.select_related():
                tt.append(t.alias_display())
            s = a_join(tt[0:2])
            if self.target.count() > 1:
                s += " (%s)" % self.target.count().__str__()
            return s


class AdType(models.Model):

    ''' Type of Message advertisement '''

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    price = models.FloatField(default=0)

    def __unicode__(self):
        return self.name

    @classmethod
    def by_code(cls, code):
        ''' get AdType by code or None '''
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            return None

    @classmethod
    def find_or_create(cls, code):
        ''' get AdType by code ; create if not exist '''
        try:
            return cls.objects.get(code=code)
        except models.ObjectDoesNotExist:
            t = AdType(code=code, name=code)
            t.save()
            return t


class MessageLog(models.Model):

    ''' Textual Log of Billboard Messages '''

    sender = models.CharField(max_length=16)
    sender_member = models.ForeignKey("Member", blank=True, null=True, \
                                      related_name="%(class)s_related_sender")
    recipient = models.CharField(max_length=16)
    recipient_member = models.ForeignKey("Member", blank=True, null=True, \
                                   related_name="%(class)s_related_recipients")
    text = models.CharField(max_length=1400)
    date = models.DateTimeField()

    def __unicode__(self):
        sender = self.sender_member.alias \
                 if self.sender_member else self.sender
        recipient = self.recipient_member.alias \
                    if self.recipient_member else self.recipient
        return u"%(sender)s > %(recipient)s: %(text)s" \
               % {'sender': sender, 'recipient': recipient, \
                  'text': self.text[:20]}


class BulkMessage(models.Model):

    ''' Outgoing message storage for delayed sending '''

    STATUS_CHOICES = (
        ('P', 'Pending'),
        ('E', 'Error'),
        ('S', 'Sent'),
    )

    sender = models.ForeignKey("Member", \
                               related_name="%(class)s_related_sender")
    recipient = models.CharField(max_length=16)
    text = models.CharField(max_length=1400)
    date = models.DateTimeField()
    status = models.CharField(max_length=1, \
                              choices=STATUS_CHOICES, default='P')

    def __unicode__(self):
        return u"%(sender)s > %(recipient)s: %(text)s" \
               % {'sender': self.sender, 'recipient': self.recipient, \
                  'text': self.text[:60]}


class Configuration(models.Model):

    ''' Key, Value storage for config variables '''

    key = models.CharField(max_length=16, primary_key=True)
    value = models.CharField(max_length=100)

    def __unicode__(self):
        return self.key

    @classmethod
    def get_dictionary(cls):
        ''' get all configuration items at once.

        return dictionary '''
        dico = {}
        for conf in cls.objects.all():
            dico[conf.key] = conf.value
        return dico
