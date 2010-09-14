#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# maintainer: dgelvin

'''
Defines the LoggedMessage model and two custom managers, (OutgoingManager and
IncomingManager
'''

from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Reporter, PersistantConnection


class OutgoingManager(models.Manager):
    '''
    A custom manager for LoggedMessage that limits query sets to
    outgoing messages only.
    '''

    def get_query_set(self):
        return super(OutgoingManager, self).get_query_set() \
                        .filter(direction=LoggedMessage.DIRECTION_OUTGOING)


class IncomingManager(models.Manager):
    '''
    A custom manager for LoggedMessage that limits query sets to
    incoming messages only.
    '''

    def get_query_set(self):
        return super(IncomingManager, self).get_query_set() \
                        .filter(direction=LoggedMessage.DIRECTION_INCOMING)


class LoggedMessage(models.Model):
    '''
    LoggedMessage model with the following fields:
        date        - date of the message
        direction   - DIRECTION_INCOMING or DIRECTION_OUTGOING
        text        - text of the message
        backend     - the backend slug of the message backend (a string)
        identity    - identity (ie. phone number) of the message (a string)
        reporter    - foreign key to Reporter from the reporters app
        status      - stores message status, (success, error, parse_error, etc)
        response_to - recursive foreignkey to self. Only used for outgoing
                      messages. Points to the LoggedMessage to which the
                      outgoing message is a response.

    Besides the default manager (objects) this model has to custom managers
    for your convenience:
        LoggedMessage.incoming.all()
        LoggedMessage.outgoing.all()
    '''

    class Meta:
        '''
        Django Meta class to set the translatable verbose_names and to create
        permissions. The can_view permission is used by rapidsms to determine
        whether a user can see the tab. can_respond determines if a user
        can respond to a message from the log view.
        '''
        verbose_name = _(u"logged message")
        verbose_name = _(u"logged messages")
        ordering = ['-date', 'direction']
        permissions = (
            ("can_view", _(u"Can view")),
            ("can_respond", _(u"Can respond")),
        )


    DIRECTION_INCOMING = 'I'
    DIRECTION_OUTGOING = 'O'

    DIRECTION_CHOICES = (
        (DIRECTION_INCOMING, _(u"Incoming")),
        (DIRECTION_OUTGOING, _(u"Outgoing")))

    #Outgoing STATUS types:
    STATUS_SUCCESS = 'success'
    STATUS_WARNING = 'warning'
    STATUS_ERROR = 'error'
    STATUS_INFO = 'info'
    STATUS_ALERT = 'alert'
    STATUS_REMINDER = 'reminder'
    STATUS_LOGGER_RESPONSE = 'from_logger'
    STATUS_SYSTEM_ERROR = 'system_error'

    #Incoming STATUS types:
    STATUS_SUCCESS = 'success'
    STATUS_MIXED = 'mixed'
    STATUS_PARSE_ERRROR = 'parse_error'
    STATUS_BAD_VALUE = 'bad_value'
    STATUS_INAPPLICABLE = 'inapplicable'
    STATUS_NOT_ALLOWED = 'not_allowed'

    STATUS_CHOICES = (
        (STATUS_SUCCESS, _(u"Success")),
        (STATUS_WARNING, _(u"Warning")),
        (STATUS_ERROR, _(u"Error")),
        (STATUS_INFO, _(u"Info")),
        (STATUS_ALERT, _(u"Alert")),
        (STATUS_REMINDER, _(u"Reminder")),
        (STATUS_LOGGER_RESPONSE, _(u"Response from logger")),
        (STATUS_SYSTEM_ERROR, _(u"System error")),

        (STATUS_MIXED, _(u"Mixed")),
        (STATUS_PARSE_ERRROR, _(u"Parse Error")),
        (STATUS_BAD_VALUE, _(u"Bad Value")),
        (STATUS_INAPPLICABLE, _(u"Inapplicable")),
        (STATUS_NOT_ALLOWED, _(u"Not Allowed")))

    date = models.DateTimeField(_(u"date"), auto_now_add=True)
    direction = models.CharField(_(u"type"), max_length=1,
                                 choices=DIRECTION_CHOICES)
    text = models.TextField(_(u"text"))
    backend = models.CharField(_(u"backend"), max_length=75)
    identity = models.CharField(_(u"identity"), max_length=100)
    reporter = models.ForeignKey(Reporter, verbose_name=_(u"reporter"),
                                 blank=True, null=True)
    status = models.CharField(_(u"status"), max_length=12,
                              choices=STATUS_CHOICES, blank=True, null=True)

    response_to = models.ForeignKey('self', verbose_name=_(u"response to"),
                                    related_name='response', blank=True,
                                    null=True)

    #Setup a default manager
    objects = models.Manager()


    # Setup custom managers.  These allow you to do:
    #    LoggedMessage.incoming.all()
    # or
    #    LoggedMessage.outgoing.all()
    incoming = IncomingManager()
    outgoing = OutgoingManager()

    def ident_string(self):
        '''
        Returns a string for the message identity.
        If there is no reporter, it will just return something like:
            dataentry 1234

        If there is a reporter, but no location it will return:
            dataentry 1234 (John Doe)

        If there is a reporter and a location it will return:
            dataentry 1234 (John Doe from New York)
        '''
        string = u"%(backend)s %(identity)s" % \
                 {'backend': self.backend, 'identity': self.identity}

        if self.reporter:
            reporter_string = self.reporter.full_name()
            if self.reporter.location:
                reporter_string = _(u"%(reporter)s from %(location)s") % \
                                  {'reporter': reporter_string,
                                   'location': self.reporter.location.name}
            string = u"%(current)s (%(reporter)s)" % \
                     {'current': string, 'reporter': reporter_string}
        return string

    def is_incoming(self):
        '''
        Returns true if this is the log of an incoming message, else false
        '''
        return self.direction == self.DIRECTION_INCOMING

    def __unicode__(self):
        return  u"%(direction)s - %(ident)s - %(text)s" % \
                 {'direction': self.get_direction_display(),
                  'ident': self.ident_string(),
                  'text': self.text}

    @classmethod
    def create_from_message(cls, message):
        '''
        Takes a rapidsms.message object and returns a new LoggedMessage
        object from it.  You _must_ set the direction of the LoggedMessage, as
        we can't tell from the message object if it is incoming or outgoing.

        It will try to check to see if a reporter exists for this message,
        and if one does, it will set the reporter foreign key of the
        LoggedMessage object to that reporter. We can't just use
        message.connection.reporter because that doesn't exist until the
        reporters app has handled the message, and we assume we want the
        logger_ng app to be the _first_ app in our local.ini.
        '''
        backend_slug = message.connection.backend.slug
        identity = message.connection.identity
        try:
            reporter = PersistantConnection \
                                .objects.get(backend__slug=backend_slug,
                                             identity=identity).reporter
        except PersistantConnection.DoesNotExist:
            reporter = None

        msg = LoggedMessage(text=message.text,
                            backend=backend_slug,
                            identity=identity,
                            reporter=reporter,
                            status=message.status)
        return msg

    @classmethod
    def tag_message(cls, message, status):
        '''
        This allows apps to easily tag _incoming_ messages they receive
        with a status.  Tagging outgoing messages is easy, you just do
        message.respond(string, status), but tagging _incoming_ messages is
        more tricky.  This classmethod does it for you.

        From your app, once you have handled the incoming message, simply call
        LoggedMessage.tag_message(message, <status>)

        i.e.
        LoggedMessage.tag_message(message, LoggedMessage.STATUS_SYSTEM_ERROR)
            or
        LoggedMessage.tag_message(message, LoggedMessage.STATUS_SUCCESS)

        This will use the logger_id watermark in the Message object to
        lookup the corresponding LoggedMessage object and set its status
        accordingly.
        '''
        if not hasattr(message, 'logger_id'):
            return
        try:
            msg = cls.objects.get(pk=message.logger_id)
        except cls.DoesNotExist:
            # If a LoggedMessage doesn't exist, we can't tag it. We'll just
            # fail silently.
            return

        msg.status = status
        msg.save()
