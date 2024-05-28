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

``-Q <KEY=VALUE>``
------------------

Override the answer to a new project prompt with the provided value.

For instance, if ``-Q "license=MIT license`` is specified, then the question to
choose a license will not be presented to the user and the MIT license will be
automatically used for the project. When used in conjunction with ``--no-input``,
the provided value overrides the default answer.

The expected keys are specified by the cookiecutter template being used to
create the new project. Therefore, the set of possible keys is not listed here
but should be expected to remain consistent for any specific version of
Briefcase; with version changes, though, the keys may change.

Third-party Bootstraps
======================

When you run new project wizard, you are asked to select a GUI toolkit. Briefcase
includes bootstraps for `Toga <https://toga.readthedocs.io>`__ (BeeWare's cross-platform
GUI framework), `PySide6 <https://wiki.qt.io/Qt_for_Python>`__ (Python bindings for the
Qt GUI toolkit) and `Pygame <https://www.pygame.org/news>`__ (a common Python game
development toolkit), as well as an "empty" bootstrap that doesn't include any GUI code.
However, Briefcase provides a :ref:`plug-in interface <bootstrap-interface>` that allows
GUI toolkits to provide a their own bootstrap implementation.

The following third-party bootstraps are known to exist:

=================================== ============== ===================================================
Bootstrap                           Package name   Description
=================================== ============== ===================================================
`PursuedPyBear <https://ppb.dev>`__ ``ppb``        "Unbearably fun game development". A game toolkit
                                                   with a focus on being education friendly and
                                                   exposing an idiomatic Python interface.
----------------------------------- -------------- ---------------------------------------------------
`Pygame-ce <https://pyga.me>`__     ``pygame-ce``  A fork of pygame, the classic library for making
                                                   games in Python.
=================================== ============== ===================================================

To add a third-party bootstrap, ``pip install`` the named package into the virtual
environment that contains Briefcase, then run ``briefcase new``. The new bootstrap
option should be added to the list of GUI toolkits.
