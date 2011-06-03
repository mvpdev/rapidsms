childcount.helpers
==============================

**PLEASE DO NOT PUT INDICATOR LOGIC HERE!!!** 
The helpers module is *only* for reusable logic that:

#. Cannot be elegantly expressed in terms of a 
   :class:`childcount.indicator.Indicator`.

#. Are used in many different reports or 
   forms.

Any function that operate on lists of 
:class:`childcount.models.Patient` objects, or
that involves DB heavy lifting should probably 
be written as a
:class:`childcount.indicator.Indicator`.
That way you get the benefits of caching and the
standardized 
:class:`childcount.indicator.Indicator` interface.


childcount.helpers.chw
-----------------------
.. automodule:: childcount.helpers.chw
    :members:
    :undoc-members:


childcount.helpers.patient
----------------------------
.. automodule:: childcount.helpers.patient
    :members:
    :undoc-members:


childcount.helpers.site
----------------------------
.. automodule:: childcount.helpers.site
    :members:
    :undoc-members:


