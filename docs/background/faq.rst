Frequently Asked Questions
==========================

What version of Python does Briefcase support?
----------------------------------------------

Python 3.5 or higher.

What platforms does Briefcase support?
--------------------------------------

Briefcase currently has support for:

  * macOS (producing DMG files, or raw .app files)
  * Linux (producing AppImage files)
  * Windows (producing MSI installers)
  * iOS (producing Xcode projects)

Support for Android will be added in the near future. Support for other some
other packaging formats (e.g., NSIS installers for Windows; Snap and Flatpak
installers for Linux) and other operating systems (e.g., tvOS, watchOS, WearOS)
are on our roadmap.

Briefcase's platform support is built on a plugin system, so if you want to add
support for a custom platform, you can do so; or, you can contribute the
backend to Briefcase itself.

How do I detect if my app is running in a Briefcase-packaged container?
-----------------------------------------------------------------------

Briefcase adds a `PEP566 <https://www.python.org/dev/peps/pep-0566/>`_
metadata file when it installs your app's code. The metadata can be retrieved
at runtime as described in the :ref:`Accessing Briefcase packaging metadata at
runtime <access-packaging-metadata>` how-to. You can determine if your
app was packaged with Briefcase by testing for the existence of
the ``Briefcase-Version`` tag::

	  in_briefcase = 'Briefcase-Version' in metadata
