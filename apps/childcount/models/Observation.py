#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Observation - Observations store
'''

from django.db import models


class Observation(models.Model):

    '''Stores observations in a key/values format

    name - the full name/description of the observation
    letter - the short code alphabet of the observation
    '''

    uid = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    letter = models.CharField(max_length=2, unique=True)

    class Meta:
        app_label = 'childcount'
        ordering = ('name',)

    def __unicode__(self):
        return self.name
