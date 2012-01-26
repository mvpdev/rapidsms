#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Event(models.Model):

    ''' Stores a dated state of an UPS device '''

    STATE_ONLINE = 1
    STATE_OFFLINE = 0

    STATE_CHOICES = (
        (STATE_OFFLINE, _(u"off-line")),
        (STATE_ONLINE, _(u"on-line")),)

    class Meta:
        get_latest_by = 'date'

    device = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    state = models.SmallIntegerField(choices=STATE_CHOICES)
    battery_present = models.BooleanField()
    battery_full_capacity = models.IntegerField(null=True, blank=True)
    battery_current_capacity = models.IntegerField(null=True, blank=True)
    requested = models.BooleanField(default=False)

    def __unicode__(self):
        return _(u"%(dev)s %(state)s on %(date)s%(requested)s") \
               % {'dev': self.device, \
                  'state': self.verbose_state,
                  'date': self.date.strftime("%R"),
                  'requested': _(u"/R") if self.requested else _(u" ")}

    def verbose(self):
        ''' Human readable sentence describing the event '''
        percent = (self.battery_current_capacity * 100) \
                   / self.battery_full_capacity
        return _(u"UPS %(device)s is now %(state)s (%(date)s). " \
                 "%(percent)s%% left. Battery: %(battery)s. " \
                 "Charge: %(cur)s/%(full)s. %(req)s") % \
               {'device': self.device,
                'state': self.verbose_state,
                'date': self.date.strftime("%x %X"),
                'percent': percent.__str__(),
                'battery': _(u"yes") if self.battery_present else _(u"no"),
                'cur': self.battery_current_capacity,
                'full': self.battery_full_capacity,
                'req': _(u"Upon request.") if self.requested else _(u" ")}

    @property
    def verbose_state(self):
        ''' human readable state of power '''
        for s in self.STATE_CHOICES:
            if s[0] == self.state:
                return s[1]
        return _(u"unknown")
