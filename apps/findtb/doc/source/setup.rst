**************
Setup
**************

#. Install :doc:`dependancies <big_picture>`.

#. Put at least the following apps in local.ini::

        apps=logger,bonjour,admin,webapp,locations,reporters,ajax,findtb,eqa,sref,notice,doc

#. Setup the db and :doc:`celery <install_celery>` 

#. Syncdb then run south migrations
