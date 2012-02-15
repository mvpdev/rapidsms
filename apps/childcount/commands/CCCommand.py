#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin

"""Module defining ChildCount+ command object."""

class CCCommand(object):
    """CCCommand is the abstract base
    class used to define new SMS commands.

    Command definitions should inherit from
    CCCommand, should define KEYWORDS 
    and should implement the `self.process`
    method.
    """

    KEYWORDS = {}
    """A dictionary of two-character language
    codes to a list of keyword names for this
    command.
    For example the command "FAMILY" might
    have a KEYWORDS that looks like::

        KEYWORDS = {
            'en': ['family', 'fam'],
            'fr': ['famille', 'fam'],
        }

    """

    message = None
    """The `rapidsms.Message` object
    that is being processed by this
    command.
    """

    params = None
    """A list of parameters to this
    command -- like the `sys.argv`
    for a python script.
    """

    def __init__(self, message, params):
        """Load command data.

        :param message: The SMS object that called this command
        :type message: rapidsms.Message
        :param params: A list of "arguments" to this command
                       (like :attr:`sys.argv`)
        :type params: list
        """
        
        self.message = message
        self.date = self.message.date
        self.params = params

    def process(self):
        """Run the command.

        You should override this method
        in your command definition.

        :returns: True if command is successful
                  (otherwise raises an exception)

        """

        pass

