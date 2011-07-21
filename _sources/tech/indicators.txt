Indicators
==============

Overview
--------------

As described in :ref:`what-is-childcount`, ChildCount+
collects data, runs analysis on those data, then generates
reports and alerts based on the results of the analysis.
The indicators functionality takes care of the simple
data analysis that goes on inside of ChildCount+.

The data analysis features are centered around the idea
of "indicators." 
An indicator is a function that takes two arguments:
a data set and a time period and returns a numerical
value.
For example, an indicator 
called "Number of Households" would take a
list of patients and a time period as arguments,
and would return an integer -- the number of 
households heads in the patient list at the given
time period -- as output.

The standard interface for indicators provides a 
few benefits to the programmer:

#. We can transparently cache indicator values. 

#. Aggregation is simple: the same indicator function
   can generate per-patient, per-CHW, per-village,
   and per-site values, depending on the patient (or other)
   list you provide as input.

#. It is easy to reuse reporting code across indicators.

The indicators code lives in two places. The
definition of the indicators interface is 
in a library directory: :file:`lib/indicator/`
while the ChildCount+ indicator definitions
live inside the ChildCount+ application
directory: :file:`apps/childcount/indicators/`.

Creating an Indicator
-------------------------

All of the ChildCount+ indicator code resides in the
:file:`apps/childcount/indicators/` directory.
For the most part, one indicator module (e.g., 
:class:`childcount.indicators.household` directly
corresponds to one ChildCount+ SMS form
(e.g., ``+V`` or the 
:class:`childcount.forms.HouseholdVisitForm`).
To create a new indicator, you must add a new class
to one of the files in :file:`apps/childcount/indicators/`.

.. warning:: Calculating indicator values can be very nuanced
             and tricky. Please make sure to extensively test
             your indicator code before you deploy it.

For example, you might want to create an indicator that
measures the number of households headed by people over
the age of 50 (at the end of the time period).
Since this indicator relates most directly to registration
(the ``+NEW`` form), we would put it in the file
:file:`apps/childcount/indicators/registration.py`.

.. warning:: If your indicator returns a percentage value,
             make sure that your indicator class inherits
             from :class:`indicator.indicator.IndicatorPercentage`.
             Using the percentage class will save you lots
             of time and will make caching your life easier!

Adding a time period
--------------------------

Since all indicators take a time period as an argument,
ChildCount+ defines a standard set of time periods we
can use for indicator and report generation.
Every time period has a start and end :class:`datetime` object,
plus one or more sub-periods.

A time period might be "One Year" and the sub-periods might
be each of the months of the year.
These time periods are defined in 
:file:`apps/reportgen/timeperiods/definitions/`.

To define a new time period, clone one of the files
in :file:`apps/reportgen/timeperiods/definitions/`, 
edit it to do what you want,
and make sure to add it to the list of imports
in :file:`apps/reportgen/timeperiods/__init__.py`.

