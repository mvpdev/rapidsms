Development Processes
===========================


Bug Tracker
----------------

You can find our bug tracker at: `<http://code.mvpafrica.org/>`_.


Mailing List
------------------

We do not have a public developer mailing list (yet). 
You can reach the ChildCount+ developers on our internal
mailing list at dev at mvpafrica dot org.

Repo and Branches
------------------------

**Repositories**

The ChildCount+ code repository is online here:

    `<http://www.github.com/mvpdev/rapidsms>`_

The installation and server configuration files for 
ChildCount+ installations are online here:

    `<http://www.github.com/mvpdev/rapidsms-impl>`_

**Branches**

The ChildCount+ code repository has two 
two main branches: `ccdev <http://www.github.com/mvpdev/rapidsms/tree/ccdev>`_ and
`ccstable <http://www.github.com/mvpdev/rapidsms/tree/ccstable>`_.
   
If a software developer wants to create a new ChildCount+ feature, the process
generally goes like this:

#.  Developer creates a new branch from ``ccdev``, let's call
    this branch
    ``twitter`` and pretend that it adds some `Twitter <http://www.twitter.com/>`_
    functionality to ChildCount+.

#.  Developer does the work on the ``twitter`` branch, merging
    changes from ``ccdev`` into ``twitter`` to make sure that 
    ``twitter`` stays current.

#.  When the developer is satisfied that the Twitter feature works
    as hoped, she merges ``twitter`` into the ``ccdev`` branch.

#.  Every few months, the release developer merges all of the changes
    from ``ccdev`` into ``ccstable``. 
    The release developer tests all of these features and makes sure
    that the translations and localization works properly for 
    French- and Tigrinya-speaking sites.

#.  The release developer writes up a textual description of how to
    update the server to accommodate the new code and posts it
    on `<http://we.mvpafrica.org>`_.

#.  The release developer pushes the ``ccstable`` code out to the
    sites. In MVP lingo, this is a "stage".



Documentation
-------------------

This documentation is hosted on `GitHub <http://www.github.com/>`_
and is created using `Sphinx <http://sphinx.pocoo.org/>`_.

We develop the documentation on the ``ccdev`` branch, then
built HTML documentation files into the root of the
``gh-pages`` branch.
The ``gh-pages`` branch
is a special branch for the `GitHub Pages <http://pages.github.com/>`_
feature. Files pushed there end up being served at
`<http://mvpdev.github.com/rapidsms/>`_.
The documentation mirror at `<http://docs.childcount.org/>`_
should copy the documentation from `<http://mvpdev.github.com/rapidsms/>`_
after every commit to the GitHub repository.

Who to Contact
-------------------

The best way to get in touch with the ChildCount+ Developers
is to look for the contact information 
listed on `<http://www.childcount.org/>`_.
Those contacts are the most likely to be up to date.
You can also catch us at `@childcount <http://www.twitter.com/childcount/>`_.




