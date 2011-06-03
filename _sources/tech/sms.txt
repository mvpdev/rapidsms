SMS and the Router
==================

Understanding the Router
-------------------------

.. _tech__sms__forms_and_commands:

SMS Forms and Commands
-----------------------

Form versus Commands
^^^^^^^^^^^^^^^^^^^^^^


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

