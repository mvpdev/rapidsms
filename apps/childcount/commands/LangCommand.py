#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.utils.translation import ugettext as _, activate

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated


class LangCommand(CCCommand):
    '''  '''

    KEYWORDS = {
        'en': ['lang'],
        'fr': ['lang'],
    }

    @authenticated
    def process(self):

        chw = self.message.persistant_connection.reporter.chw

        # warn if no lang specified
        if self.params.__len__() < 2:
            self.message.respond(_(u"Lang command requires language code "), \
                                   'error')
            return True

        newlang = self.params[1].strip()

        if chw.language == newlang:
            self.message.respond(_(u"Your language is already set " \
                                   "to %(lang)s") % {'lang': chw.language})
            return True

        if newlang not in self.KEYWORDS:
            self.message.respond(_(u"The new language code (%(code)s) is " \
                                   "not valid. ") % {'code': newlang})
            return True

        oldlang = chw.language
        chw.language = newlang
        chw.save()
        activate(chw.language)
                
        self.message.respond(_(u"Your language preference has been changed " \
                                "from %(old)s to %(new)s. ") % \
                                {'old': oldlang, 'new': chw.language})

        return True
