#!/usr/bin/env python
# -*- coding= UTF-8 -*-

import numpy
from datetime import time, date, datetime, timedelta

from django_tracking.models import TrackedItem, State
from .models import Specimen
from django.db import models

class ProxySpecimen(Specimen):
    class Meta:
        proxy = True

    @property
    def tracker(self):
        return TrackedItem.get_tracker(self)

    def get_state_date_with_title(self, title):
        try:
            state = self.tracker.states.exclude(type='alert').get(title=title)
        except State.DoesNotExist:
            return None
        return state.created

    @staticmethod
    def filter_by_dates(specimens, date_start, date_end):
        if isinstance(date_start, date):
            date_start = datetime.combine(date_start, time())
        if isinstance(date_end, date):
            date_end = datetime.combine(date_end, time(hour=23,minute=59))

        return filter(lambda x: x.registered >= date_start and
                                x.registered <= date_end, specimens)

    @property
    def sent(self):
        return self.get_state_date_with_title('sent')

    @classmethod
    def number_sent(cls, date_start=None, date_end=None):
        specimens = filter(lambda x: x.sent != None,
                           ProxySpecimen.objects.all())

        if date_start and date_end:
            specimens = ProxySpecimen.filter_by_dates(specimens, date_start,
                                                      date_end)
        return len(specimens)

    @property
    def time_for_delivery(self):
        if self.sent and self.received:
            return self.received - self.sent

    @classmethod
    def get_stats(cls, state, origin, location=None, cutoff=None,
                  date_start=None, date_end=None):
        states = State.objects.filter(title=state, origin=origin) \
                              .exclude(type='alert') \
                              .exclude(cancelled=True)

        items = []
        for state in states:
            ti = state.tracked_item
            co = ti.content_object
            if location and \
                location not in co.location.ancestors(include_self=True):
                continue
            if date_start and state.created < date_start:
                continue
            if date_end and state.created > date_end:
                continue
            all_states = list(ti.states.exclude(type='alert') \
                                       .exclude(cancelled=True) \
                                       .order_by('created'))
            try:
                previous_state = all_states[all_states.index(state)-1]
            except IndexError:
                continue
            items.append({'co':co,
                          'duration': state.created - previous_state.created})

        stats = {'num': len(items)}
        if len(items) == 0:
            return stats

        items.sort(key=lambda x: x['duration'])
        stats['items'] = [item['co'] for item in items]
        stats.update({'min': items[0]['duration'], 'min_item': items[0]['co']})
        stats.update({'max': items[-1]['duration'], 'max_item': items[-1]['co']})

        durations = [item['duration'] for item in items]
        dsum = timedelta()
        for d in durations:
            dsum += d
        stats['avg'] = dsum / len(durations)

        stats['med'] = timedelta(seconds= \
                numpy.median([d.seconds + d.days * 86400 for d in durations]))

        if cutoff:
            items_before = [item['co'] for item in \
                              filter(lambda x: x['duration'] <= cutoff, items)]
            stats['items_before_cutoff'] = items_before
            stats['num_before_cutoff'] = len(items_before)

            items_after = [item['co'] for item in \
                              filter(lambda x: x['duration'] > cutoff, items)]
            stats['items_after_cutoff'] = items_after
            stats['num_after_cutoff'] = len(items_after)

        return stats

        
        

    @classmethod
    def stats_for_delivery(cls, cutoff=None, date_start=None, date_end=None):
        specimens = filter(lambda x: x.time_for_delivery != None,
                           ProxySpecimen.objects.all())

        if date_start and date_end:
            specimens = ProxySpecimen.filter_by_dates(specimens, date_start,
                                                      date_end)

        if len(specimens) == 0:
            return 0, 0, None, None, None, None

        if cutoff:
            in_cutoff = len(filter(lambda x: x.time_for_delivery <= cutoff, 
                                   specimens))
        else:
            in_cutoff = len(specimens)
        specimens.sort(key=lambda x: x.time_for_delivery)

        min = specimens[0].time_for_delivery
        max = specimens[-1].time_for_delivery

        avg = timedelta()
        for s in specimens:
            avg += s.time_for_delivery
        avg = avg / len(specimens)
        med = timedelta(seconds= \
                numpy.median([x.time_for_delivery.seconds + \
                              x.time_for_delivery.days * 86400 \
                              for x in specimens]))
        return len(specimens), in_cutoff, min, max, med, avg


    @property
    def received(self):
        return self.get_state_date_with_title('received')

    @property
    def time_for_microscopy(self):
        if self.received and self.microscopy:
            return self.microscopy - self.received

    @classmethod
    def stats_for_microscopy(cls, cutoff=None, date_start=None, date_end=None):
        specimens = filter(lambda x: x.time_for_microscopy != None,
                           ProxySpecimen.objects.all())

        if date_start and date_end:
            specimens = ProxySpecimen.filter_by_dates(specimens, date_start,
                                                      date_end)

        if len(specimens) == 0:
            return 0, 0, None, None, None, None

        if cutoff:
            in_cutoff = len(filter(lambda x: x.time_for_microscopy <= cutoff,
                                   specimens))
        else:
            in_cutoff = len(specimens)

        specimens.sort(key=lambda x: x.time_for_microscopy)

        min = specimens[0].time_for_microscopy
        max = specimens[-1].time_for_microscopy

        avg = timedelta()
        for s in specimens:
            avg += s.time_for_microscopy
        avg = avg / len(specimens)
        med = timedelta(seconds= \
                numpy.median([x.time_for_microscopy.seconds + \
                              x.time_for_microscopy.days * 86400 \
                              for x in specimens]))
        return len(specimens), in_cutoff, min, max, med, avg

    @property
    def microscopy(self):
        return self.get_state_date_with_title('microscopy')



