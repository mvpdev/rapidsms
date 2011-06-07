RapidSMS Overview
==================

ChildCount is built using the `RapidSMS <http://www.rapidsms.org/>`_
framework.
The following few sections will introduce you to a few key
RapidSMS concepts: the router, backends, and applications.

Router
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
-------------------

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
-----------------------

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

As in Django, you can have many RapidSMS apps running on the same
ChildCount+ server.
The order in which the apps get to handle messages is determined
by the order in which they appear in the :file:`local.ini` file.

Some useful SMS-related apps are: 

* :doc:`/apps/childcount </api/apps/childcount/index>` -- Handles all ChildCount+ messages

* :file:`/apps/fortune` -- Responds to the message :command:`FORTUNE` with
  a Ugandan proverb

* :file:`/apps/logger_ng` -- Stores all messages in a message log database table

* :file:`/apps/ping` -- When it receives a message :command:`PING`, it responds :command:`PONG`

.. _tech__sms__forms_and_commands:


The ChildCount+ Application
=============================

The body of the ChildCount+ message processing
happens in :file:`/apps/childcount/app.py` -- 
ChildCount's RapidSMS application.
The following sections describe how components
*within* the ChildCount+ application 
process messages and how you can customize
these components. 

SMS Forms and Commands
---------------------------------

To understand ChildCount+ SMS processing, you
must know the difference between a *form*, 
a *command*, and a *report*.

.. caution:: We have recklessly overloaded the term "form."
             The word "form" can refer to the paper paper forms 
             filled out by CHWs (see: :ref:`human__forms`) or
             it can refer to SMS forms -- the logic that parses
             and processes messages (described below).


Forms and commands are both means of connecting
SMS keywords to bits of application processing logic.
The difference is that SMS *forms* are part of a
message that begins with a
patient health identifier (health ID) and (*commands*)
are consist of messages that begin with a keyword.

.. list-table:: Examples of SMS Commands
    :header-rows: 1

    *
        - Message Sent to Server
        - Action Taken by Server
    *
        - ``CHECKID abc123``
        - Reply to sender with a message explaining
          whether or not the health ID ``abc123`` is valid.
    *   
        - ``LOOKUP joe``
        - Reply to sender with a message listing all
          of the patients with name ``joe``.
    *
        - ``CANCEL``
        - Cancel the effect of the sender's previous
          message.

As you see, all of the commands listed in the table
begin with a keyword (like ``CHECKID``).
Commands are useful for situations where the message
does not directly relate to a registered patient.
Commands inherit from the class :class:`childcount.commands.CCCommand`.

Other commands are listed in the commands
API documentation (:doc:`/api/apps/childcount/commands`)
and in the ChildCount+ source code in the folder
:file:`/apps/childcount/commands`.

Messagings containing
SMS forms begin with a valid ChildCount+ health ID
(see :ref:`human__health_ids`), followed by a 
series of +CODE sequences.
ChildCount+
checks the validity of the health ID before any
of the form processing logic begins.

The SMS forms generally correspond to fields
on the paper ChildCount+ forms.
For example, the ``+V`` form below
corresponds to the ``+V`` section of the
ChildCount+ household visit form (paper form B).
You can look at the paper forms here:
:ref:`human__forms`.

.. list-table:: 
    :header-rows: 1

    * 
        - Message Sent to Server
        - Action Taken by Server

    *
        - ``ABC123 +V Y 2 BN FP``
        - Record that the CHW who sent the message
          conducted a household visit at the household
          headed by the person whose health ID is
          ``ABC123``.
          The arguments to the ``+V`` form indicate that
          there was a household member present (``Y``),
          that there were two under-fives present (``2``),
          and that the CHW discussed bednets and family
          planning (``BN FP``) at the household visit.
    *
        - ``56HG2 +F Y +S FV VM +R B``
        - Record that the patient with health ID ``56HG2``
          tested positive with a rapid diagnostic test
          for malaria (``+F Y``), that the patient
          has fever and is vomiting (``+S FV VM``), and
          that the CHW made a 24-hour referral for this
          patient to a health center (``+R B``).

Note that it is possible (and encouraged) to
send many forms relating to the same patient within
the same message.
Combining forms this way cuts down on the number of
SMS messages that CHWs need to send per household 
visit.

SMS forms reside in the directory
:file:`apps/childcount/forms` and the API documentation
is here: :doc:`/api/apps/childcount/forms`.
SMS forms inherit from :class:`childcount.forms.CCForm`.

You enable commands and forms by including them in the
list of active commands/forms in the :file:`local.ini`
configuration file.

SMS Reports
-------------

.. caution::    We have shamelessly overloaded the term "report:"
                The word "report" can refer to the printed paper
                reports generated by ChildCount+ (see :doc:`/tech/reports`)
                or it can refer to Report models (described below).

Reports (in the context of messaging) are Django models
for storing information collected from a ChildCount+
SMS form.
In general, the form holds parsing and validation logic for
the collected data,
while the report is where the data ends up being stored.
A "report" in this context is a Django model that corresponds
to a database table holding the form data.

For example, the ``+V`` SMS form collects data about household
visits.
There is a class :class:`childcount.forms.HouseholdVisitForm`
that defines the parsing and validation logic for the ``+V`` form.
Once the data has been parsed from the ``+V`` form and validated,
it is stored using the Django ORM as a 
:class:`childcount.reports.HouseholdVisitReport` object.

All of the ChildCount+ reports are 
located in :file:`apps/childcount/models/reports.py`,
and they inherit from `childcount.models.CCReport`.


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

Adding a New Form
^^^^^^^^^^^^^^^^^^^^^^

