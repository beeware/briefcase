=====
macOS
=====

The default output format for macOS is an :doc:`app <./app>`.

Briefcase also supports creating an :doc:`Xcode project <./xcode>`
which in turn can be used to build an app.

Both output formats support packaging as a macOS DMG or as a standalone
signed app bundle.

.. toctree::
   :maxdepth: 1

   app
   xcode

Platform quirks
===============

Requirements cannot be provided as source tarballs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Briefcase *cannot* install packages published as source tarballs into a macOS app, even
if the package is a pure Python package that would produce a ``py3-none-any`` wheel.
This is an inherent limitation in the use of source tarballs as a distribution format.

If you need to install a package in a macOS app that is only published as a source
tarball, you'll need to compile that package into a wheel first. If the package is pure
Python, you can generate a ``py3-none-any`` wheel using ``pip wheel <package name>``. If
the project has a binary component, you will need to consult the documentation of the
package to determine how to compile a wheel.

You can then directly add the wheel file to the ``requires`` definition for your app, or
put the wheel in a folder and add:

.. code-block:: TOML

    requirement_installer_args = ["--find-links", "<path-to-wheel-folder>"]

to your ``pyproject.toml``. This will instruct Briefcase to search that folder for
compatible wheels during the installation process.
