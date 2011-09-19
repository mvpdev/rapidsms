Installation Instructions
==========================

ChildCount+ is not easy to install, so make sure you have
a patient Linux-savy software developer or server administration
on hand before you get started.

`Millennium Villages Project <http://www.millenniumvillages.org/>`_
has an internal wiki where we keep the latest documentation on
how to deploy ChildCount+.
Here are the key pages:

* `Installing ChildCount+ and RapidSMS <http://we.mvpafrica.org/mhealth+mctc/installation>`_ 
  (for the Web interface and database)

* `Installing Celeryd and RabbitMQ <http://we.mvpafrica.org/mhealth+mctc/installing-celery>`_
  (for reports and SMS alerts -- follow instructions for "The Champion's Way")

There are lots of steps involved in setting up and maintaining a ChildCount+
server.
If (by some miracle) you are able to get ChildCount+ running, you can take a look at
the various server configuration files used at the Ruhiira, Uganda installation
here:

    `Ruhiira Install Files <https://github.com/mvpdev/rapidsms-impl/tree/master/childcount-2.0/ruhiira>`_

The best way to get help with the installation is to contact one of the ChildCount+
developers directly.
Since the team is always in flux, check the `ChildCount+ Web site <http://www.childcount.org/>`_
to find out how to contact us.


Running the Software
=======================

Once everything is installed, you can use the following commands
to start your ChildCount+ instance::
    
    sudo service rabbitmq-server start
    sudo service celeryd start
    sudo service celery-beat start
    sudo service rapidsms start
    sudo service rapidsms-webserver start

You then should then open a browser and navigate to::

    http://your_server_ip/childcount

The normal Django administration pages are at::

    http://your_server_ip/admin


