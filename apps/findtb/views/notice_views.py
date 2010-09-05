#!/usr/bin/env python
# -*- coding= UTF-8 -*-

import re
from datetime import datetime

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required

from rapidsms.webui.utils import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from findtb.models import Notice
from findtb.libs.utils import send_msg


@login_required
@permission_required('findtb.change_notice')
def notices(request, *arg, **kwargs):

    if request.method == 'POST':
        for field, value in request.POST.iteritems():
            match = re.match(r'^response_(?P<id>\d+)$', field)
            if match and len(value) > 1:
                pk = match.groupdict()['id']
                n = get_object_or_404(Notice, pk=pk)
                response = value[:159]
                if not n.response:
                    n.response = response
                    n.responded_by = request.user
                    n.responded_on = datetime.now()
                    send_msg(n.reporter, response)
                    n.save()

        return redirect("findtb-notices")

    new_notices = Notice.objects.filter(response=None).order_by('recieved_on')
    old_notices = Notice.objects.exclude(response=None).order_by('-responded_on')
    notices = list(new_notices) + list(old_notices)

    paginator = Paginator(notices, 15)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        notices = paginator.page(page)
    except (EmptyPage, InvalidPage):
        notices = paginator.page(paginator.num_pages)


    ctx = {'notices':notices}
    ctx.update(kwargs)

    return render_to_response(request, "notices.html", ctx)
