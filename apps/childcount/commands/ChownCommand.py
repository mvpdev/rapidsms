#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

import datetime

from django.utils.translation import ugettext as _

from childcount.commands import CCCommand
from childcount.models import Patient, CHW
from childcount.utils import authenticated

class ChownCommand(CCCommand):
    ''' Change CHW for a patient set

        Format: chown FIRST_ID LAST_ID
        Sets all patients created between
        FIRST_ID and LAST_ID (inclusive)
        by the same CHW/Data entry clerk 
        to the current CHW.

        Alt. format: chown HEALTH_ID
        Change patient with specified
        heath id to be same as current
        CHW.
    '''

    KEYWORDS = {
        'en': ['chown'],
        'rw': ['chown'],
        'fr': ['chown'],
    }

    @authenticated
    def process(self):
        if 'encounter_date' not in self.message.__dict__:
            self.message.respond(_(u'Cannot run chown command from '
                                    'cell phone. Use the computer interface '
                                    'instead.'), 'error')
            return True

        # warn if no search criteria
        if self.params.__len__() < 2:
            self.message.respond(_(u"Lookup command requires at least one " \
                                   "health ID."), 'error')
            return True

        # lookup CHW
        try:
            new_chw = CHW.objects.get(pk = self.message.chw)
        except CHW.DoesNotExist:
            self.message.respond(_(u"CHW with ID %(id)d does not exist") % \
                {'id': self.message.chw})
            return True

        terms = self.params[1:]
        first_id = terms[0].upper()

        if len(terms) < 2:
            last_id = None
        else:
            last_id = terms[1].upper()

        first = None
        last = None

        # Lookup first health id
        try: 
            first = Patient.objects.get(health_id=first_id)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': first_id}, 'error')
            return True

        if last_id is None:
            first.chw = new_chw
            first.save()
            self.message.respond(_(u"Patient %(hid)s (%(name)s) assigned to CHW " \
                                    "%(chwname)s.") % \
                                        {'hid': first_id.upper(),
                                        'name': first.full_name(),
                                        'chwname': new_chw.full_name()}, 
                                    'success')
            return True

        # Lookup last health id
        try: 
            last = Patient.objects.get(health_id=last_id)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': last_id}, 'error')
            return True
  
        if first.chw.pk != last.chw.pk:
            self.message.respond(_(u"Patients %(first)s and %(last)s have " \
                                    "different CHWs.  (First CHW: %(fchw)s " \
                                    "Last CHW: %(lchw)s)") % 
                                    {'first': first.health_id.upper(),
                                    'last': last.health_id.upper(),
                                    'fchw': first.chw, 'lchw': last.chw}, 'error')
            return True
        
        if first.created_on > last.created_on:
            self.message.respond(_(u"Patient %(fid)s was created " \
                "AFTER patient %(lid)s. You should send the earlier ID first " \
                "followed by the later ID.") % \
                    {'fid': first_id, 'lid': last_id},
                'error')
            return True

        matches = Patient.objects\
            .filter(chw=first.chw.pk)\
            .filter(created_on__gte=first.created_on)\
            .filter(created_on__lte=last.created_on)

        if matches.count() == 0:
            self.message.respond(\
                _(u"There were 0 patients created by CHW %(chw)s " \
                "between %(fdate)s and %(ldate)s.") \
                % {'chw': unicode(first.chw),
                    'fdate': unicode(first.created_on),
                    'ldate': unicode(last.created_on)}, \
                'error')

            return True
        nrows = matches.update(chw = new_chw)

        ''' Get current encounter date '''
        parts = self.message.encounter_date.split('-')
        parts = map(int, parts)

        ''' Set encounter dates to current date '''
        for p in matches:
            e = p.encounter_set.order_by('encounter_date')[0]
            if len(parts) != 3:
                self.message.respond(\
                _(u"Encounter date %(date)s is not valid") % \
                    {'date': self.message.encounter_date})
                return True
            e.encounter_date = datetime.datetime(*parts)
            e.save()

        self.message.respond(\
            _(u"Changed CHW for %(n)d patients to %(chw)s" 
                u" with encounter date %(y)d-%(m)d-%(d)d.") \
                % {'n': nrows, 
                    'chw': unicode(new_chw),
                    'y': parts[0],
                    'm': parts[1],
                    'd': parts[2]},
            'success')

        return True
