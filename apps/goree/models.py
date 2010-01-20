#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models
from rapidsms.webui.managers import *




class Horaire(models.Model):
    """A Location is technically a geopgraphical point (lat+long), but is often
       used to represent a large area such as a city or state. It is recursive
       via the _parent_ field, which can be used to create a hierachy (Country
       -> State -> County -> City) in combination with the _type_ field."""

    sitedepart = models.CharField(max_length=100)
    sitearrivee = models.CharField(max_length=100)
    datedepart = models.CharField(max_length=100)
   
    
    
    def __unicode__(self):
        return self.sitedepart
    
