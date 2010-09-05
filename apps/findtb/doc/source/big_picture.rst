**********************
Global overview of the project
**********************

Concepts
============================

There is a lot of code but the principle is simple:

**EQA** is a part of the application that deals with quality assessement. It's
mostly traking slides from one place to another by sms
and then enter tests results in a web form.
 
**Specimen referal** (sref) is a part of the application that deals with tuberculosis testing.
There is a few tracking with SMS, but most of the work is on forms saving tests results.

**Specimens and slides are associated to states**, from the django_tracking application.
States are generic data holder that are bind to another object (using django generica relations)
and let you retrace the history of all what it did. e.g : we use it for tracking 
and display the history of events in the dashboard.

Every generic state is linked to a real object representing the state, you'll find all
of them in 'models'. It means there is a table for every state. It can seem a waste,
but it has a lot of nice side effects, like letting you storing any data the way you want
for each state. Querying can be troublesome for special case, but for most usages, 
it straightforward. 

All the sms are processed by app.py that delegates the work in functions in the 
'handler' module

In the tracking views, every real state object holds the information of 
which form to display on the web site, and it's name is used to choose the view
to use. 

e.g: in sref, if the speciment passed microscopy, it's current state is 
"MicroscopyResults". MicroscopyResults state, according to previous results,
choose to display either the for for LJ or MGIT.

Knowing that, most of the code is:

* checking if somebody can do somethin by sms
* changing the state of the specimen / slides
* display the right data on the we site

Dependencies
==================

**Python modules:**

Core:

    * Python==2.6 (multiprocessing needed for celery)
    * Django==1.1.2
    * rapidsms==0.1 (can't be installed using pip or easy_install)
    * MySQL-python==1.2.3c1 (production only, , can run without it in dev)

For the search engine:

    * Whoosh==0.3.18 
    * django-haystack==1.0.1-final

Alerts:

    * django-celery==2.0.0
    * python-dateutil==1.4.1
    * ghettoq=0.4.1

Logistics:

    * South==0.7.1 (only for database migration, can run without it)
    * Sphinx==1.0b2 (only for documentation, can run without it)
    * Werkzeug==0.6.2 (dev only, can run without it in prod)
    * django-debug-toolbar==0.8.3 (dev only, , can run without it in prod)
    * django-extensions==0.5 (dev only, , can run without it in prod)


It runs fine using virtualenv.

