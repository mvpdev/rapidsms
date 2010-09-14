#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from datetime import datetime

import rapidsms
from scheduler.models import EventSchedule

from mgvmrs.forms import *
from mgvmrs.utils import *
from mgvmrs.encounters import *


def loop2mn(loop):
    ''' Generates an array of numbers for Event Schudule minutes '''

    try:
        loop = int(loop)
    except:
        loop = 5

    mn = []
    for num in range(0, 60):
        if num % loop == 0:
            mn.append(num)
    return mn


class App (rapidsms.app.App):
    ''' Configures MGVMRS

    Configures config values from local.ini
    Provide a way to trigger Encounter queue processing '''

    def configure(self, individual_id=1, household_id=1, location_id=1, \
                  interval=30, *args, **kwargs):
        self.individual_id = int(individual_id)
        self.household_id = int(household_id)
        self.location_id = int(location_id)
        self.interval = int(interval)

    def start(self):
        # set up a every <interval> minutes to generate/send xforms to omrs
        try:
            EventSchedule.objects.get(\
                                     callback="mgvmrs.encounters.send_to_omrs")
        except EventSchedule.DoesNotExist:
            schedule = EventSchedule(\
                                   callback="mgvmrs.encounters.send_to_omrs", \
                                   minutes=set(loop2mn(self.interval)))
            schedule.save()

    def handle(self, message):
        # debug only.
        if not message.text == 'omrs process encounters queue':
            return False

        message.respond(u"Launching Encounters queue processing.")
        send_to_omrs(self.router)
        message.respond(u"Encounters queue processed.")

        
