Indicators
==============

[U] Overview
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

#. Having a standard interface makes it easy to generate
   reports for any indicator without having to write
   custom reporting code.

The indicators code lives in two places. The
definition of the indicators interface is 
in a library directory: :file:`lib/indicator/`
while the ChildCount+ indicator definitions
live inside the ChildCount+ application
directory: :file:`apps/childcount/indicators/`.

[U] Creating an Indicator
-------------------------

(which in code is a class that 
inherits from :class:`indicator.indicator.Indicator`)


[U] Adding a time period
--------------------------


