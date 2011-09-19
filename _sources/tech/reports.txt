Printed Reports
==================================

Overview
----------

Printed report generation is arguably the most important thing that
ChildCount+ does. 
To simplify the process, we have created a report generation "framework"
of sorts that makes creating reports faster and easier (once you know
how it all works).

One key principle of the framework to reduce the duplication of code
by abstracting a lot of the common elements of report generation out
of the individual report code.
The framework treats each report as a function that takes
as arguments:

#. A time period (e.g., "12 Months (divided by Quarter)")
#. A file format (e.g., "pdf")
#. [Optional] A variant (e.g., "Bugongi Health Center")

In the definition of the report, the report author only has to
write a function that takes these three parameters and spits
out a report with the desired properties.
The report framework handles the user interface for generating
reports and manages the storage as well.
Look at the existing reports to see how this all is done.


How to Add Reports
--------------------------

#. Create a report definition file and place it in :file:`apps/reportgen/definitions`.
   Your best bet is to copy an existing report file and adjust it according to your needs.

#. If your report is called :file:`NewReport.py`, then add :class:`NewReport` to
   the :class:`__all__` list in :file:`apps/reportgen/definitions/__init__.py`.

#. Open the Django admin interface (at http://your_server_ip/admin), and add an entry
   to the Reportgen.Report model. The entry should contain the name of your report
   class (e.g., :class:`NewReport`) and a human-readable title for the report.

#. Restart :file:`celeryd`, :file:`rapidsms` and :file:`celerybeat`.


How to Debug Reports
-----------------------

Debugging reports can be annoying. The one way to simplify the process is this::

    # Open shell
    cd sms
    ./rapidsms shell

    # Load a time period
    from reportgen.timeperiods import Month
    t = Month.periods()[2]

    # Load your new report definition file
    from reportgen.definitions.MyNewReport import ReportDefinition
    
    # Test the report using the first variant
    ReportDefinition.test(t, 'pdf')
    
    # The generated report will end up in /tmp/test_my_new_report
    # (or whatever the name of your report is)
    
    # To re-run your report, you need to quit the shell
    exit

Save this script in a file to speed up the process.

ccdoc - ChildCount+ Document-Generation Library
------------------------------------------------

The ccdoc library adds another layer of abstraction to reports.
Using ccdoc, you can generate an instance of a report as a ccdoc
:class:`ccdoc.document.Document` object and ccdoc will handle
generation of the report output in HTML, PDF, and XLS file
formats.
Many of the reports in :file:`apps/reportgen/definitions`
use ccdoc to simplify the report generation process and those
are good places to look for real-world examples of ccdoc in
action.

The file :file:`lib/ccdoc/example.py` contains an example of
how to create and render a Document into HTML.  Run the
example from your rapidsms shell (when you're in your site
directory) like this::

    cd ~/your-site
    ./rapidsms shell < lib/ccdoc/example.py > test.html
    # Ignore the >>> prompts that the python shell adds 

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
