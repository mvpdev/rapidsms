Reports, Celery and RabbitMQ
============================

Overview
----------

Installation
-------------
#. See Dickson's page on how to install celery
#. sudo service rabbitmq-server start
#. sudo service celeryd start



How to Add/Debug Reports
--------------------------


ccdoc - ChildCount+ Document-Generation Library
==================================================

Introduction
-----------------

The goal of ccdoc is to provide a simple way for ChildCount+
users to generate customized and printable data reports and
documents.


Install
---------

Put the ccodc folder in the lib folder of your
rapidsms/django site directory.  That is:
    your-site/lib/ccdoc/

Requires:
- reportlab for PDFs
- xlwt for Excel files


An Example
-----------

The file example.py in this folder contains an example of
how to create and render a Document into HTML.  Run the
example from your rapidsms shell (when you're in your site
directory) like this:

./rapidsms shell < lib/ccdoc/example.py


How It Works
-------------

The user creates a Document object, which is pretty much a
collection of Section, Paragraph, and Table objects.  The
user then passes the Document to an object that inherits from
Generator (for example, HTMLGenerator).  The Generator
object prints the formatted report to a file -- you can either
ask for the name of the file where the report has been printed
or you can get the contents of the file back as a string.

You can create new Generator objects that inherit from
Generator.  If you do, make sure to look in generator.py at
the bottom and to implement _*_document() and the _render_*()
methods in your subclass.


