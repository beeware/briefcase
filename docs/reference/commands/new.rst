===
new
===

Start a new Briefcase project. Runs a wizard to ask questions about your new
application, and creates a stub project using the details provided.

Usage
=====

To start a new application, run::

    $ briefcase new

Options
=======

The following options can be provided at the command line.

``-t <template>`` / ``--template <template>``
---------------------------------------------

A local directory path or URL to use as a cookiecutter template for the new
project. Briefcase will attempt to use a template branch matching the version
of Briefcase that is being used (i.e., if you're using Briefcase 0.3.9,
Briefcase will use the `v0.3.9` template branch when generating the app).
If you're using a development version of Briefcase, Briefcase will use the
`main` branch of the template.
