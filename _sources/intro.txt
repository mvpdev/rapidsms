
Introduction
============

Target Audience
---------------

This documentation is meant for **programmers** and **project managers**
who are interested in deploying ChildCount+.
Project managers and health professionals might focus on 
the :doc:`human` section.
Programmers and medical records specialists can focus on
the :doc:`tech/index` section.


What is ChildCount+?
--------------------

ChildCount+ [#f1]_ is a health data management
system designed for day-to-day use by community health workers.
To be specific, ChildCount+:

#. Collects health information from community health workers 
    (by text message or paper forms),

#. Sends text message alerts to health workers and health managers,

#. Calculates the values of key health and CHW performance indicators
    using data collected from the CHWs, and

#. Produces concise printed performance reports for CHWs and their managers.



Workflow
--------

ChildCount+'s original design revolved around mobile phones: 
community health workers would submit information to the ChildCount+
server by text message (SMS).
Based on the submitted data, the server would then periodically
send information and alerts to the community health workers.
The ChildCount+ deployment in `Sauri, Kenya <http://millenniumvillages.org/the-villages/sauri-kenya/>`_,
where Millennium Villages Project first piloted ChildCount+, uses
the mobile-phone-based workflow depicted in the 
:ref:`accompanying figure <diagram_mobile>`.



.. _diagram_mobile:

.. figure:: images/intro/diagram_mobile.png
    :scale: 60%
    :alt: ChildCount+ mobile data flow diagram.

    A representation of the mobile-phone-based ChildCount+ workflow.


It is possible to deploy ChildCount+ without mobile phones.
In fact, most Millennium Village sites use a 
:ref:`paper-based workflow <diagram_dataentry>`
for ChildCount+, since managing airtime credit and fleet of mobile phones
is sometimes not possible.


.. _diagram_dataentry:

.. figure:: images/intro/diagram_dataentry.png
    :scale: 60%
    :alt: ChildCount+ paper-based data flow diagram.

    A representation of the paper-based ChildCount+ workflow.


What's in the Box 
-----------------

The two major open-source components of ChildCount+ are:

* **Paper Forms**: See :ref:`human__forms` to check out
  our paper data collection forms.

* **Software**: See the :doc:`tech/index` section for details
  on our software and what you need to get it up and running.

For everything else (community health workers, data entry clerks,
programmers, servers, mobile phones, airtime, ...) you are on
your own!


Should You Use ChildCount+?
---------------------------

Here are some questions to consider before embarking on a ChildCount+
deployment:

* **Do you have a community health worker program?**
    If not, ChildCount+ might not be the best platform for your project.
    You can customize ChildCount+ to suit your application (tracking
    levels of drug stocks, for example) but that would require extensive
    programming and customization.
    See :ref:`human__prereqs` for more information.

* **Do you have health managers with enough time to maintain the system?**
    Many of the Millennium Village Project sites aim to have feedback
    meetings with the community health workers *every month*.
    If you have scores of CHWs distributed over a large geographical
    area, these meetings can take a non-trivial amount of time.
    Don't bother deploying the system if you don't have time to use
    the data it produces.
    See :ref:`human__prereqs` for more information.
    
* **Do you have a technical team (or at least a technical person)?**
    ChildCount+ is not a "plug-and-play" solution.
    In fact, it is more like "download-and-hack" solution.
    You will need, at least, 
    one on-call Python programmer with some Linux systems
    administration experience to install the software 
    and to maintain the server.
    See :ref:`human__prereqs` for more information.

* **Do you have money to pay for paper and SMS fees?**
    

* Do you have enough cell phones for your CHWs?

* Do you have a system in place to manage airtime for CHWs?

* Do you have the means (i.e., transport) to meet regularly with your CHWs?


Deployment Background
---------------------

`Millennium Villages Project <http://www.millenniumvillages.org/>`_
has deployed ChildCount+ at its sites across sub-Saharan Africa.
As of May 2011, these deployments are the *only* ChildCount+
deployments.
For more information on the history of ChildCount+, please see
:doc:`history`.



.. rubric:: Footnotes

.. [#f1] **Why the +?** We call our system ChildCount+ 
    (read: "Child count plus") because it has expanded from
    a system for collecting data about children to a system
    for collecting data about people -- including adults.
    The "+" represents the fact that we count children *and*
    adults too.

