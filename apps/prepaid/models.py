#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' Prepaid App Models

Configuration
MessageLog - Text log of prepaid messages
Record - Action log of prepaid sessions '''

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Configuration(models.Model):

    ''' Key, Value storage for config variables '''

    key = models.CharField(max_length=32, primary_key=True)
    value = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.key

    @classmethod
    def get(cls, key):
        ''' get arbitrary config item from key code.

        return dictionary or None'''
        try:
            return cls.get_dictionary(cls)[key]
        except:
            return None

    @classmethod
    def get_dictionary(cls):
        ''' get all configuration items at once.

        return dictionary '''
        dico = {}
        for conf in cls.objects.all():
            dico[conf.key] = conf.value
        return dico


class MessageLog(models.Model):

    ''' Raw Log of textual informations from message. '''

    sender = models.CharField(max_length=16)
    recipient = models.CharField(max_length=16)
    text = models.CharField(max_length=1400)
    date = models.DateTimeField()

    def __unicode__(self):
        return u"%(sender)s > %(recipient)s: %(text)s" \
               % {'sender': self.sender, 'recipient': self.recipient, \
                  'text': self.text[:20]}


class Record(models.Model):

    ''' Log of Prepaid Actions '''

    TYPE_CHOICES = (
        ('T', 'Top Up'),
        ('B', 'Balance'),
    )

    sender = models.CharField(max_length=16)
    text = models.CharField(max_length=1400)
    date = models.DateTimeField()
    kind = models.CharField(max_length=1, choices=TYPE_CHOICES, \
                                       default='B')
    value = models.FloatField()

    def __unicode__(self):
        return u"%(sender)s> %(kind)s = %(value)s - %(text)s" \
               % {'sender': self.sender, 'kind': self.kind, \
                  'value': self.value, 'text': self.text[:60]}
