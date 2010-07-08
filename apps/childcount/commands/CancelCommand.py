#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from reversion import revision
from reversion.models import Revision, Version

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.exceptions import Inapplicable


class CancelCommand(CCCommand):

    KEYWORDS = {
        'en': ['cancel'],
        'fr': ['cancel', 'annuler'],
    }

    # The time (in minutes) during which a report can be canceled.
    CANCEL_TIMEOUT_MIN = 10

    @authenticated
    def process(self):

        # Let's start by turning off revision control for this cancel command.
        # We'll handle all the revision / version stuff manually here.
        # Something nasty may happen if we change a bunch of versions while
        # we are in revision control.
        revision.invalidate()

        user = self.message.persistant_connection.reporter.user_ptr

        if not Revision.objects.filter(user=user).count():
            raise Inapplicable(_(u"Cancel failed. There is nothing to " \
                                  "cancel."))

        # Get the last revision created by this user (reporter)
        last_rev = Revision.objects.filter(user=user).latest('date_created')
        if last_rev.date_created + \
           timedelta(minutes=self.CANCEL_TIMEOUT_MIN) < datetime.now():
            raise Inapplicable(_(u"Cancel failed. You cannot cancel a " \
                                 "report after %(num)d minutes.") %\
                                 {'num': self.CANCEL_TIMEOUT_MIN})

        # If the current version's revision is not equal to the last revision
        # by this user then someone else has modified it since.  This could
        # get ugly, so let's not go there.
        for v in last_rev.version_set.all():
            obj = v.object_version.object
            current_rev = Version.objects \
                                 .get_for_date(obj, datetime.now()).revision

            cls = v.content_type.model_class()
            pk = v.object_id

            if current_rev != last_rev or \
               not cls.objects.filter(pk=pk).count():
                raise Inapplicable(_(u"Cancel failed. Another user has " \
                                      "already modified one or more of your " \
                                      "reports."))

        for v in last_rev.version_set.all():
            cls = v.content_type.model_class()
            pk = v.object_id
            try:
                obj = cls.objects.get(pk=pk)
            except cls.DoesNotExist:
                continue

            v_list = Version.objects \
                       .get_for_object(obj).order_by('-revision__date_created')

            if v_list.count() == 1:
                obj.delete()
            else:
                previous_version = v_list[1]
                previous_version.revert()

        last_rev.delete()

        self.message.respond(_(u"Previous message successfully canceled."), \
                             'success')

        return True
