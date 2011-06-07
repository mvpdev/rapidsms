SMS and the Router
==================

The Router
-------------------------

The [RapidSMS] router is the part of ChildCount+ that handles incoming
and outgoing messages, and it operates independently from
whatever Web server you are using to view the ChildCount+ dashboard.
(Other parts of ChildCount+ serve Web pages and generate
analytical reports.)
If you are deploying ChildCount+ yourself, you will probably
want to learn how to use the router to respond to special
SMS keywords or to collect deployment-specific data.
See the SMS section of :ref:`tech__understanding`
for an overview of the router.

Backends
---------

The RapidSMS router interacts with the outside world
via a set of "backends" (whoever chose this terminology
must have had a sense of humor...).

An application that uses SMS, Web data entry, and email
to interact with the world would have three backends:
one for each of these three transport mechanisms.
Backends inherit from :class:`rapidsms.backends.backend.Backend`
and they use a common interface to tell the RapidSMS
router how to send and receive messages.
The active backends are specified in the :file:`local.ini`
file in the root ChildCount+ directory.

Applications
---------------

The router treats incoming messages the same way no
matter where they come from (by SMS, email, etc) --
every message gets parsed into a :class:`rapidsms.message.Message`
object and handed to the active applications.

As described in :ref:`tech__understanding`, RapidSMS
steps through the active applications listed
in the :file:`local.ini` file and calls :meth:`[app_name].App.handle`
on each, with the :class:`rapidsms.message.Message` object
as an argument.
Each application processes the message and returns ``False``
if the message should be passed on to the rest of the
active applications, and ``True`` otherwise.

Here is an example :meth:`App.handle` definition
that responds to a message :command:`FLIP` with the
message :command:`Heads` or :command:`Tails`::

    class App(rapidsms.app.App):
        def handle(self, message):
            if message.text.strip().upper() == "FLIP":
                response = random.choice(["Heads", "Tails"])
                message.respond(response)
                return True
            else:
                return False



.. _tech__sms__forms_and_commands:

SMS Forms, Commands, and Reports
---------------------------------

To understand ChildCount+ SMS processing, you
must know the difference between a *form*, 
a *command*, and a *report*.
Forms and commands are both means of defining
special SMS keys

Adding a New Form
^^^^^^^^^^^^^^^^^^^^^^


Defining a Command
^^^^^^^^^^^^^^^^^^^^^^

Say you want to define a new command called `ReverseTextCommand`
that users invoke by SMS like this::

    REVERSE First Second Third


To define this command, you must:

#. Look through the existing commands in :file:`apps/childcount/commands`
   to make sure that the command you want does not already exist.
   There are lots of useful commands defined there, so please check first.

#. Create a file :file:`apps/childcount/commands/ReverseTextCommand.py`

#. Within this new file, import :class:`childcount.commands.CCCommand`
   and define a new class that inherits from it::


    from childcount.commands import CCCommand
    from childcount.utils import authenticated

    class ReverseTextCommand(CCCommand):

        KEYWORDS = {
            'en': ['reverse'],
            'fr': ['inverse'],
        }

        @authenticated
        def process(self):
            ...do actual work here

   See :ref:`api__childcount__commands__CCCommand` for the definition
   of the :class:`childcount.command.CCCommand` class.

#. In :file:`apps/childcount/commands/__init__.py`, add the line::

    from childcount.commands.ReverseTextCommand import ReverseTextCommand

#. In your :file:`local.ini` file in the root ChildCount+ directory,
   add :class:`ReverseTextCommand` to the list of active commands::

    ...
    [childcount]
    commands = WhoCommand, LookupCommands, ReverseTextCommand, ...
    ...

.. _tech__sms__forms_to_database:

From Forms to the Database
---------------------------


