
Human Aspects
===============

.. _human__prereqs:

Human Prerequisites
-------------------

.. warning:: Even the simplest mobile health
             platform will probably require a full-time or near-full-time
             manager to keep it running and to integrate it into 
             your existing health program.
             Do not spend time and money deploying a mobile health
             system if you do not have the human resources to 
             make it useful!

Community health workers
    ChildCount+ is a tool for community health workers to
    keep track of their patients and for health managers
    to keep track of their community health workers.
    ChildCount+ is not a general data collection tool
    (for that, see `ODK <http://opendatakit.org/>`_)
    nor is it a tool that would be very useful for
    clinicians or for general-purpose medical record keeping
    (for that, see `OpenMRS <http://openmrs.org/>`_).

Programmers
    Running ChildCount+ requires access to a software
    developer or at least a systems administrator.
    The more programming talent you have at your disposal,
    the more flexible and useful ChildCount+ will
    become.
    ChildCount+ is written in the `Python <http://www.python.org/>`_
    programming language and uses the `Django <http://www.djangoproject.com/>`_
    and `RapidSMS <http://www.rapidsms.org/>`_ frameworks,
    so people with knowledge of those technologies will be
    particularly useful.

    `FrontlineSMS <http://www.frontlinesms.com/>`_ might
    be a good alternative solution for organizations without
    programmers at their disposal.


Community Health Worker Program
-------------------------------

Since we designed ChildCount+ for the 
`Millennium Villages Project <http://www.millenniumvillages.org/>`_,
we have incorporated elements of the MVP CHW protocols into
the ChildCount+ forms, alerts, and reports.


.. _human__health_ids:

Health IDs
-----------------

One important and time-consuming part of the
ChildCount+ set-up process is patient registration.
Each person who is to be tracked by the ChildCount+
system must be assigned a unique ChildCount+ health identifier.
Our deployments use the Childcount form `+NEW`
(:class:`childcount.forms.PatientRegistrationForm`) to
assign health IDs to patients.

These health idenfiers are like primary keys into a database
table -- each person's health identifier is unique within
the system and is the most common way to 
reference to their patient record.

The Millennium Villages Project deployments use the 
`OpenMRS IdGen Module <https://wiki.openmrs.org/display/docs/Idgen+Module>`_
to generate the health IDs and we use the
Luhn-30 checksums to validate the IDs.


.. _human__forms:

Forms
-----

Here are examples of the ChildCount+ forms we use:

**All Sites**

* :download:`Danger Signs List </files/forms/DangerSigns_v2.0.pdf>`

**Sauri, Kenya**

* :download:`Form A (Patient Registration) </files/forms/sauri/A_v2.0_Sauri.pdf>`

* :download:`Form B (Household Visit and Family Planning) </files/forms/sauri/B_v2.0_Sauri.pdf>`

* Form C (Consultation)

  - :download:`Children </files/forms/sauri/Ca_v2.0_Sauri.pdf>`
  
  - :download:`Pregnant Women </files/forms/sauri/Cb_v2.0_Sauri.pdf>`

* :download:`Form HED (Household Associationg) </files/forms/sauri/HED_v2.0_Sauri.pdf>`

* Form P (Pregnancy Forms)

  - :download:`P: Demographics </files/forms/sauri/P_v2.0_Sauri.pdf>`
  
  - :download:`P2: Initial Antenatal Visit </files/forms/sauri/P2_v2.0_Sauri.pdf>`
  
  - :download:`P2: Follow-up Visit </files/forms/sauri/P3_v2.0_Sauri.pdf>`

* :download:`Form R (Appointment Reminder Log) </files/forms/sauri/R_v2.0_Sauri.pdf>`

* :download:`Form V (Clinic Visit Log) </files/forms/sauri/V_v2.0_Sauri.pdf>`


**Ruhiira, Uganda**

* :download:`Form A (Patient Registration) </files/forms/ruhiira/A_v2-1_Ruhiira_EN.pdf>`

* :download:`Form B (Household Visit) </files/forms/ruhiira/B_v2-1_Ruhiira_EN.pdf>`

* :download:`Form C (Consultation) </files/forms/ruhiira/C_v2-1_Ruhiira_EN.pdf>`

* :download:`Correction </files/forms/ruhiira/Correction_v2-1_Ruhiira_EN.pdf>`




