#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Config Model for child count

'''

from django.db import models
from django.utils.translation import ugettext as _


class Configuration(models.Model):

    '''Store Key/value childcount config options'''

    key = models.CharField(_('Key'), max_length=50, db_index=True)
    value = models.CharField(_('Value'), max_length=255, \
                             db_index=True, blank=True)
    description = models.CharField(_('Description'), max_length=255, \
                                   db_index=True)

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_config'
        unique_together = ('key', 'value')

    def __unicode__(self):
        return u"%s: %s" % (self.key, self.value)

    def get_dictionary(self):
        return {'key': self.key, 'value': self.value, \
                'description': self.description}

    @classmethod
    def get(cls, key=None):
        '''get config value of specified key'''
        cfg = cls.objects.get(key=key)
        return cfg.value
