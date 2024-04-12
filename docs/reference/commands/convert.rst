=======
convert
=======

Convert an existing project with a ``pyproject.toml`` configuration into a project that
can be deployed with Briefcase. Runs a wizard to ask questions about your existing
application (reading from the ``pyproject.toml`` file where applicable), adds the
necessary files to the project, and updates the ``pyproject.toml`` file to include the
``briefcase`` section.

Usage
=====

To convert your application, run the following command in the application root
directory (where the ``pyproject.toml`` file is located):

.. code-block:: console

    $ briefcase convert

Options
=======

The following options can be provided at the command line.

``-t <template>`` / ``--template <template>``
---------------------------------------------

A local directory path or URL to use as a cookiecutter template for the
project.

``--template-branch <branch>``
------------------------------

The branch of the cookiecutter template repository to use for the project.
If not specified, Briefcase will attempt to use a template branch matching the
version of Briefcase that is being used (i.e., if you're using Briefcase 0.3.14,
Briefcase will use the ``v0.3.14`` template branch when generating the app). If
you're using a development version of Briefcase, Briefcase will use the ``main``
branch of the template.

``-Q <KEY=VALUE>``
------------------

Override the answer to a prompt with the provided value.

For instance, if ``-Q "license=MIT license"`` is specified, then the question
to choose a license will not be presented to the user and the MIT license will
be automatically used for the project. When used in conjunction with
``--no-input``, the provided value overrides the default answer.

The expected keys are specified by the cookiecutter template being used to
create a new project (the same cookiecutter template is used here). Therefore,
the set of possible keys is not listed here but should be expected to remain
consistent for any specific version of Briefcase; with version changes, though,
the keys may change.
