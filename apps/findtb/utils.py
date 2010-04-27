#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from functools import wraps

from django.utils.translation import ugettext as _

import rapidsms

from findtb.exceptions import NotRegistered

class Keyworder(object):

    def __init__(self):
        self.regexes = {}

    def __call__(self, *regex_strs):
        def decorator(func):
            for regex in regex_strs:
                if len(regex) == 0:
                    continue
                if regex[-1] != '$':
                    regex = regex + '$'
                if regex[0] != '^':
                    regex = '^' + regex
                self.regexes[regex] = func
            return func
        return decorator

    def get_function(self, keyword):
        for regex, func in self.regexes.iteritems():
            if re.match(regex, keyword):
                return func
        return None

    def is_valid_keyword(self, keyword):
        return self.get_function(keyword) != None

def clean_msg(text):
    # If the message is only white space, change it to None
    if re.match(r'^\s*$', text):
        return None

    # make lower case, strip, and remove duplicate spaces
    return re.sub(r'\s{2,}', ' ', text.strip().lower())      

def clean_names(flat_name, surname_first=True):

    '''
    Takes a persons name as a single string and returns surname,
    first names, and alias
        >>> clean_names("smith john")
        (u'Smith', u'John', u'jsmith')

    Also can be passed an optional argument surname_first=False:
        >>> clean_names("john ADAM smith", surname_first=False)
        (u'Smith', u'John Adam', u'jasmith')
    '''

    if not isinstance(flat_name, unicode):
        flat_name = unicode(flat_name)

    # Replace all occurances of 0 with o
    flat_name = re.sub('0', 'o', flat_name)

    # Replace all non-alphanumeric character with spaces
    flat_name = re.sub('\W_', ' ', flat_name)

    # Remove numbers
    flat_name = re.sub('\d', '', flat_name)

    # break up the name into a list
    names = re.findall('\w+', flat_name)

    surname = firstnames = alias = u''

    if names:
        pop_index = 0 if surname_first else -1
        surname = names.pop(pop_index).title()
        firstnames = ' '.join(names).title()
        alias = ''.join([c[0] for c in names] + [surname]).lower()

        if not names and not surname_first:
            surname, firstnames = firstnames, surname

    return surname, firstnames, alias

def respond_exceptions(func):

    '''
    A decorator that catches exceptions and sends the text of the exception
    to the sender by responding to the message object.  It can be used
    on the rapidsms.app.App methods that are passed (self, message)
    '''

    @wraps(func)
    def wrapper(self, *args):
        if len(args) == 0 or \
           not isinstance(args[0], rapidsms.message.Message):
            return func(self, *args)

        message = args[0]
        try:
            return func(self, *args)
        except Exception, e:
            message.respond(_(u"An error has occured (%(e)s).") % {'e': e}, \
                            'error')
            raise
    return wrapper

def restricted(func):
    '''
    A decorator that rejects users that are not registered
    '''
    @wraps(func)
    def wrapper(message):
        if message.persistant_connection.reporter:
            return func(message)
        else:
            raise NotRegistered
    return wrapper
