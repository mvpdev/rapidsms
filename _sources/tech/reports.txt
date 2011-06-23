[U] Printed Reports
==================================

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
------------------------------------------------

About ccdoc
~~~~~~~~~~~~
The goal of ccdoc is to provide a simple way for ChildCount+
users to generate customized and printable data reports and
documents.


Install
~~~~~~~~~~~

Put the ccodc folder in the lib folder of your
rapidsms/django site directory.  That is:

    :file:`your-site/lib/ccdoc/`

Requires:

* reportlab for PDFs

* xlwt for Excel files


An Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The file :file:`lib/ccdoc/example.py` contains an example of
how to create and render a Document into HTML.  Run the
example from your rapidsms shell (when you're in your site
directory) like this::

    cd ~/your-site
    ./rapidsms shell < lib/ccdoc/example.py


How It Works
~~~~~~~~~~~~~~

The user creates a :class:`ccdoc.document.Document` object, 
which is pretty much a
collection of :class:`ccdoc.section.Section`, 
:class:`ccdoc.paragraph.Paragraph`, and 
:class:`ccdoc.table.Table` objects.  The
user then passes the :class:`Document` to an object that inherits from
:class:`ccdoc.generator.Generator` (for example, 
:class:`ccdoc.html.HTMLGenerator`).  The :class:`Generator`
object prints the formatted report to a file -- you can either
ask for the name of the file where the report has been printed
or you can get the contents of the file back as a string.

You can create new :class:`Generator` objects that inherit from
:class:`Generator`.  If you do, make sure to look in 
:file:`lib/ccdoc/generator.py` at
the bottom and to implement :meth:`_*_document()` and the 
:meth:`_render_*()`
methods in your subclass.

See the :doc:`/api/lib/ccdoc` page for API information.
