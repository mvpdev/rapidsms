Understanding the ChildCount+ Technology
=========================================

Before you "get started," make sure to take a look at
the :ref:`intro__should_you_use` section of the
introduction.
If you are duly convinced that you need some CC+ action in
your life, then read on.

.. _tech__prereqs:

Technology Prerequisites
------------------------

.. warning:: ChildCount+ should NOT be deployed on 
             a publicly accessible network.
             Data between the server and clients is
             not encrypted the software is not hardened
             against attacks.

.. tip:: Wait! Before you read on, check out the 
         :ref:`human__prereqs` section.
         Make sure that you're not missing anything on the human
         side of things before you jump into the land of
         config files and list comprehensions.

Hopefully these documentation pages, plus some
Googling, will be all the information you need to get
ChildCount+ up and running.
In the real world, it is unlikely that the ChildCount+
team will be able to keep this documentation up
to date forever, but at least we are trying!

All Installs
^^^^^^^^^^^^^

Linux Server
    You will need a server to host your ChildCount+
    installation. 
    We recommend using Ubuntu versions 10 and up, 
    since that is what we use for development and deployments.

Printer
    If you need to print paper reports.

SMS-Based Installs
^^^^^^^^^^^^^^^^^^^

GSM Modem
    If you want to interact with ChildCount+ via SMS.
    Any modem that works with `PyGSM <http://pypi.python.org/pypi/pygsm/0.1>`_
    will work.
    We use Multitech MTCBA-G-F4 modems.

SMS-Enabled Mobile Phones
    One per community health worker.

Mobile Phone Chargers
    If you are deploying in an area without reliable
    power, make sure you have solar chargers or some
    other means of charging cell phones.

Airtime Credit Distribution System
    You will need some way to distribute airtime
    credit to the community health workers.
    Millennium Villages Project has tried to 
    negotiate with mobile operators to get 
    toll-free SMS lines, but distributing
    airtime scratch cards by hand is also
    an option.

Understanding the Components
-----------------------------

The ChildCount+ stack is large -- it includes many 
components patched together in non-obvious ways.
The following diagrams will hopefully give you a
sense of what the components of ChildCount+ are
and how they relate to each other.

ChildCount+ runs on top of
`RapidSMS <http://www.rapidsms.org>`_, but since
there is almost no documentation for RapidSMS,
we will try to document bits of RapidSMS as we
go along.

.. list-table:: **ChildCount+ Component Overview**
    
   * - **Web**. How ChildCount+ handles HTTP requests from
       Web browsers:

       * *Cherokee Web Server* handles incoming HTTP requests and
         passes them to...

       * *django_wsgi.py* -- a Python script that sets some environment
         variables (like the local time zone) and invokes Django's
         wsgi (Web Server Gateway Interface) handler.

       * *Django*'s Web framework handles the request from there.
         The Web portion of ChildCount+ works like Django (with a few
         caveats).
         You will find Django-style :file:`views.py` and :file:`urls.py`
         files in the :file:`apps/*` directories.

     - .. image:: /images/tech/web.jpg

   * - **SMS**. How ChildCount+ handles SMS messages.

       * The *GSM modem* receives SMS messages from your mobile operator
         and queues them.

       * *PyGSM* provides a simple API through which Python applications 
         (like RapidSMS) can connect to the GSM modem to send and receive
         SMS messages.

       * The *RapidSMS Router* (:file:`rapidsms route`)
         periodically (every five seconds or so)
         uses PyGSM to check the modem for pending incoming messages and to send
         pending outgoing messages.
         The :file:`rapidsms` program resides in the root ChildCount+
         directory and is the core RapidSMS executable.

       * The router then looks for all installed RapidSMS applications.
         The list of installed applications is in the file
         :file:`local.ini` in the root ChildCount+ directory.
         For an example of :file:`local.ini` files, see the
         `ChildCount+ Installation Repository <https://github.com/mvpdev/rapidsms-impl>`_.

       * For each installed application, RapidSMS loads the file
         :file:`apps/[app_name]/app.py` and calls the :meth:`App.handle`
         method with a :class:`rapidsms.message.Message` object.
         (:class:`App` inherits from :class:`rapidsms.app.App`.)

       * The *:meth:`App.handle`* method does app of the SMS processing logic,
         and finally returns a ``bool`` value, indicating whether RapidSMS
         should propagate the message to other installed apps (when :meth:`App.handle`
         returns ``True``) or not (when :meth:`App.handle` returns ``False``).
         The :meth:`App.handle` method can also call the :meth:`message.respond`
         method on the ``message`` object to send an SMS back to the sender.

     - .. image:: /images/tech/sms.jpg

   * - **Reports**. How ChildCount+ schedules and runs
       nightly reports and SMS alerts: 

       * Each RapidSMS application within a ChildCount+ installation
         has a file called :file:`apps/[app_name]/tasks.py`.
         `Django Celery <http://celeryproject.org/docs/django-celery/>`_
         loads these files and uses them to schedule periodic
         tasks.

       * `Celerybeat <http://celeryproject.org/>`_, a process invoked as 
         :file:`/etc/init.d/celeryd -B` periodically checks
         the current time, and the task run history located
         in (:file:`celerybeat-schedule`) to determine if there
         is a periodic task that should run.
         When Celerybeat wants to run a task, it inserts
         a message into...

       * `RabbitMQ <http://www.rabbitmq.com/>`_, a message queue that holds pending
         tasks.

       * `Celeryd <http://celeryproject.org/>`_
         worker processes periodically check
         RabbitMQ for pending tasks and they run any pending
         tasks they find in the queue.
         Celeryd workers run as :file:`/etc/init.d/celeryd`
         and can run in the same process as Celerybeat (above).
         When Celeryd workers start up, they load the current
         RapidSMS/ChildCount+ code so they have access to
         the ChildCount+ database and all ChildCount+
         classes.

       * The Celeryd workers can write out completed reports
         to the file system or they can send SMS alerts out
         via the RapidSMS messaging functionality.

     - .. image:: /images/tech/reports.jpg


Dependencies
-------------

We use:

* `Ubuntu <http://www.ubuntu.com/>`_ 10.04

* `Python <http://www.python.org/>`_ 2.6

* `Django <http://www.djangoproject.com>`_ 1.1

* `PyGSM <http://pypi.python.org/pypi/pygsm/0.1>`_ 0.1

* `RapidSMS <http://www.rapidsms.org>`_ 0 ("old core") 

* `Django Celery <http://celeryproject.org/docs/django-celery/>`_ 2.2.4

* `Celery <http://www.celeryproject.org>`_ 2.2.5

* `RabbitMQ Server <http://www.rabbitmq.com>`_ 1.6

* `Kombu <http://packages.python.org/kombu/>`_ 1.0.7

* `MySQL <http://www.mysql.com/>`_ 5.1




