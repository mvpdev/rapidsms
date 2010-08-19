#!/usr/bin/env python
# -*- coding= UTF-8 -*-

"""
Tools to handle alerts.
Related models are with tracking models for the correponding apps.
"""

import datetime

from dateutil.relativedelta import relativedelta

from django_tracking.models import TrackedItem

class AlertForBeingLate(object):
    """
    Common code to share between alerts triggered when a process is late.
    """    
    delay = relativedelta(weeks=+1)
    state_type = 'alert'
    
    
    @classmethod
    def get_deadline(cls, slides_batch=None):
        """
        Returns the date when this process was due.
        """
        if slides_batch:
            ti, c = TrackedItem.get_tracker_or_create(content_object=slides_batch)
            last_state_date = ti.get_history().exclude(type='alert')[0].created
        else:
            last_state_date = datetime.datetime.today()
        return last_state_date + cls.delay
    
    
    def _formated_deadline(self):
        """
        Get the deadline in a readable format
        """
        d = self.get_deadline(self.slides_batch)
        return d.strftime('%m/%d/%Y')
    formated_deadline = property(_formated_deadline)
