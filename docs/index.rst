.. raw:: html

    <style>
        .row {clear: both}

        .column img {border: 1px solid black;}

        @media only screen and (min-width: 1000px),
               only screen and (min-width: 500px) and (max-width: 768px){

            .column {
                padding-left: 5px;
                padding-right: 5px;
                float: left;
            }

            .column3  {
                width: 33.3%;
            }

            .column2  {
                width: 50%;
            }
        }
    </style>


=========
Briefcase
=========

Briefcase is a tool for converting a Python project into a standalone
native application. It supports producing binaries for:

* macOS, as a standalone .app;
* Windows, as an MSI installer;
* Linux, as an AppImage;
* iOS, as an XCode project; and
* Android, as a Gradle project.

It is also extensible, allowing for additional platforms and installation
formats to be produced.

.. rst-class::  row

Table of contents
=================

.. rst-class:: clearfix row

.. rst-class:: column column2

:ref:`Tutorial <tutorial>`
--------------------------

Get started with a hands-on introduction for beginners


.. rst-class:: column column2

:ref:`How-to guides <how-to>`
-----------------------------

Guides and recipes for common problems and tasks, including how to contribute


.. rst-class:: column column2

:ref:`Background <background>`
------------------------------

Explanation and discussion of key topics and concepts


.. rst-class:: column column2

:ref:`Reference <reference>`
----------------------------

Technical reference - commands, modules, classes, methods


.. rst-class:: clearfix row

Community
=========

Briefcase is part of the `BeeWare suite`_. You can talk to the community through:

 * `@pybeeware on Twitter <https://twitter.com/pybeeware>`__

 * `Discord <https://beeware.org/bee/chat/>`__

 * The Briefcase `Github Discussions forum <https://github.com/beeware/briefcase/discussions>`__

.. _BeeWare suite: http://beeware.org
.. _Read The Docs: https://briefcase.readthedocs.io


.. toctree::
   :maxdepth: 2
   :hidden:
   :titlesonly:

   tutorial/index
   how-to/index
   background/index
   reference/index
