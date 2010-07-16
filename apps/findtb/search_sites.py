#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os

from django.conf import settings

import haystack
haystack.autodiscover()

from haystack.indexes import *
from haystack import site

from django_tracking.models import TrackedItem


class TrackedItemIndex(RealTimeSearchIndex):

    text = CharField(document=True, use_template=True,
                     template_name='search/tracked_item_index.txt')

    def get_queryset(self):
        return TrackedItem.objects.order_by('-pk')


site.register(TrackedItem, TrackedItemIndex)


