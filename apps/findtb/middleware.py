#!/usr/bin/env python
# -*- coding= UTF-8 -*-

from findtb.models import Notice
from django.conf import settings

class NoticeCounterMiddleware(object):
    """
        Add the count of current notices in the tab menu.
    """
    def process_request(self, request):
        
        notices_count = Notice.objects.filter(response__isnull=True).count()

        if notices_count:
            settings.RAPIDSMS_APPS['notice']['title'] = "Notice (%s)" % notices_count

