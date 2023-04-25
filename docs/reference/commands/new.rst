===
new
===

Start a new Briefcase project. Runs a wizard to ask questions about your new
application, and creates a stub project using the details provided.

Usage
=====

To start a new application, run:

.. code-block:: console

    $ briefcase new

Options
=======

The following options can be provided at the command line.

``-t <template>`` / ``--template <template>``
---------------------------------------------

A local directory path or URL to use as a cookiecutter template for the new
project.

``--template-branch <branch>``
------------------------------

The branch of the cookiecutter template repository to use for the new project.
If not specified, Briefcase will attempt to use a template branch matching the
version of Briefcase that is being used (i.e., if you're using Briefcase 0.3.14,
Briefcase will use the ``v0.3.14`` template branch when generating the app). If
you're using a development version of Briefcase, Briefcase will use the ``main``
branch of the template.
