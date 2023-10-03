Frequently Asked Questions
==========================

What version of Python does Briefcase support?
----------------------------------------------

Python 3.8 or higher.

What platforms does Briefcase support?
--------------------------------------

Briefcase currently has support for:

* macOS (producing DMG files, or raw .app files)
* Linux (producing system packages, AppImage files or Flatpaks)
* Windows (producing MSI installers)
* iOS (producing Xcode projects)
* Android (producing Gradle projects)

Support for other some other operating systems (e.g., tvOS, watchOS, WearOS, and
the web) are on our road map.

Briefcase's platform support is built on a plugin system, so if you want to add
support for a custom platform, you can do so; or, you can contribute the
backend to Briefcase itself.

How do I detect if my app is running in a Briefcase-packaged container?
-----------------------------------------------------------------------

Briefcase adds a `PEP566 <https://peps.python.org/pep-0566/>`_ metadata file
when it installs your app's code. The metadata can be retrieved at runtime as
described in the :ref:`Accessing Briefcase packaging metadata at runtime
<access-packaging-metadata>` how-to. You can determine if your app was packaged
with Briefcase by testing for the existence of the ``Briefcase-Version`` tag::

    in_briefcase = 'Briefcase-Version' in metadata

Can I use third-party Python packages in my app?
------------------------------------------------

Yes! Briefcase uses ``pip`` to install third-party packages into your app bundle.
As long as the package is available on PyPI, or you can provide a wheel file for
the package, it can be added to the ``requires`` declaration in your
``pyproject.toml`` file and used by your app at runtime.

If the package is pure-Python (i.e., it does not contain a binary library), that's
all you need to do.

If the package contains a binary component, you'll need to ensure that a binary
wheel is available for the platform you're targeting:

* **macOS, Linux, Windows**: Binary wheels are hosted on `PyPI <https://pypi.org>`__.
* **Android**: See the :ref:`Android platform documentation
  <android-third-party-packages>`.
* **iOS**: See the :ref:`iOS platform documentation <ios-third-party-packages>`.
* **Web**: Binary wheel support is currently limited to `those provided by the Pyodide
  project <https://pyodide.org/en/stable/usage/packages-in-pyodide.html>`__.
