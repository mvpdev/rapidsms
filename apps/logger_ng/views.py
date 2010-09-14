#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
Views for logger_ng
'''

import re
from datetime import datetime, timedelta
from time import sleep

from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required, permission_required

from rapidsms.webui.utils import render_to_response
from django.http import HttpResponseRedirect

from logger_ng.models import LoggedMessage
from logger_ng.utils import respond_to_msg


@login_required
@permission_required('logger_ng.can_view')
def index(request):
    '''
    Index view
    '''
    MESSAGES_PER_PAGE = 30

    # If it is a POST then they are responding to a message.
    # Don't allow sending if the user doesn't have the can_respond permission
    if request.method == 'POST' and \
       request.user.has_perm('logger_ng.can_respond'):
        for field, value in request.POST.iteritems():
            match = re.match(r'^respond_(?P<id>\d+)$', field)
            if match and len(value) > 1:
                pk = match.groupdict()['id']
                msg = get_object_or_404(LoggedMessage, pk=pk)
                respond_to_msg(msg, value)
        return redirect(index)

    # Don't exclude outgoing messages that are a response to another,
    # because they will be shown threaded beneath the original message
    msgs = LoggedMessage.objects.exclude(
                                    direction=LoggedMessage.DIRECTION_OUTGOING,
                                    response_to__isnull=False)

    msgs.order_by('-date', 'direction')

    paginator = Paginator(msgs, MESSAGES_PER_PAGE)

    # Set the pagination page. Go to page 1 in the event there is no page
    # get variable or if it's something other than a number.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # Try to set the paginator object to the correct page. Set it to the
    # last page if there is some problem with it (too high, etc...)
    try:
        msgs = paginator.page(page)
    except (EmptyPage, InvalidPage):
        msgs = paginator.page(paginator.num_pages)

    ctx = {'msgs': msgs}
    return render_to_response(request, "logger_ng/index.html", ctx)
