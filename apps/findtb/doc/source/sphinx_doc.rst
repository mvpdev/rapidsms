******************
Sphinx basics
******************

Install sphinx::

    easy_install sphinx

Setup sphinx::

    sphinx-quickstart

Include your reST files in the main index::

    Contents:

    .. toctree::
        :maxdepth: 2
       
        name_of_your_file.rst # indent matters !
       
    Indices and tables
    ==================

Generate the doc::

    sphinx-build src_dir dest_dir

reST and Sphinx Cheat sheets:

* http://matplotlib.sourceforge.net/sampledoc/cheatsheet.html#cheatsheet-literal
* http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/tutorial/rest_syntax.html#restructured-text-rest-and-sphinx-cheatsheet
