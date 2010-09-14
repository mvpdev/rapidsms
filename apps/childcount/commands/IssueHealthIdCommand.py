#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import datetime
import random

from django.utils.translation import ugettext as _

from reporters.models import Reporter
from locations.models import Location

from childcount.commands import CCCommand
from childcount.models import CHWHealthId
from childcount.utils import authenticated


class IssueHealthIdCommand(CCCommand):

    KEYWORDS = {
        'en': ['getid'],
        'fr': ['getid'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        #Need to check if the CHW has health ids that he has not used
        if CHWHealthId.objects.filter(chw=chw, used=False):
            self.message.respond(_(u"You still have: %(health_id)s") %
                                {'health_id': ', '.join([h.health_id.health_id \
                                for h in CHWHealthId.objects.filter(chw=chw,\
                                                                used=False)])})
        else:
            #issue 5 ids
            list = CHWHealthId.objects.filter(chw=None, used=False)
            if not list:
                self.message.respond(_(u"No health Ids available now!"))
            else:
                #get a random list of 5
                if list.count() > 5:
                    ids  = random.sample(list, 5)
                else:
                    ids = random.sample(list, list.count())
                for id in ids:
                    id.chw = chw
                    id.issued_on = datetime.datetime.now()
                    id.used = False
                    id.save()
                self.message.respond(_(u"Health IDs: %(health_id)s") %
                                        {'health_id':\
                                            ', '.join([h.health_id.health_id \
                                                        for h in ids])})

        return True
