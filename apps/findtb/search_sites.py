#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os

from django.conf import settings

import haystack
haystack.autodiscover()

from haystack.indexes import *
from haystack import site

from django_tracking.models import TrackedItem


TEMPLATE_DIR = os.path.join(settings.PROJECT_ROOT, 'apps/findtb/indexes')

class TrackedItemIndex(SearchIndex):

    text = CharField(document=True, use_template=True,
                     template_name=os.path.join(TEMPLATE_DIR, 
                                                'tracked_item_index.txt'))

    def get_queryset(self):
        return TrackedItem.objects.order_by('-pk')


site.register(TrackedItem, TrackedItemIndex)


