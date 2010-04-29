#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from functools import wraps

from django.utils.translation import ugettext as _

import rapidsms

from findtb.exceptions import NotRegistered

def clean_msg(text):

    '''
    Cleans the message.  It does the following:
        - Change a message of only whitespace to ''
        - Make entire message lower-case
        - Change any series of spaces greater than 1 to just one space.
        - Strip leading and trailing whitespace
    '''
    # If the message is only white space, return an empty string
    if re.match(r'^\s*$', text):
        return ''

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
            message.respond(("An error has occured (%(e)s).") % \
                           {'e': e}, 'error')
            raise
    return wrapper

def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if sender property is set on message, and whether the parent
    user model is_active

    return function or raise exception '''

    @wraps(func)
    def wrapper(keyword, params, message):
        if message.persistant_connection.reporter and \
           message.persistant_connection.reporter.user_ptr.is_active:
            return func(keyword, params, message)
        else:
            raise NotRegistered
    return wrapper
