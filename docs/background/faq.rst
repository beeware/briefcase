Frequently Asked Questions
==========================

What version of Python does Briefcase support?
----------------------------------------------

Python 3.8 or higher.

What platforms does Briefcase support?
--------------------------------------

Briefcase currently has support for:

* macOS (producing DMG files, or raw .app files)
* Linux (producing AppImage files or Flatpaks)
* Windows (producing MSI installers)
* iOS (producing Xcode projects)
* Android (producing Gradle projects)

Support for other some other operating systems (e.g., tvOS, watchOS, WearOS, and
the web) are on our roadmap.

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


Can I use third-party Python packages in my app?
------------------------------------------------

Yes! Briefcase uses `pip` to install third-party packages into your app bundle.
As long as the package is available on PyPI, or you can provide a wheel file for
the package, it can be added to the ``requires`` declaration in your
``pyproject.toml`` file and used by your app at runtime.

If the package is pure-Python (i.e., it does not contain a binary library), that's
all you need to do.

If the package contains a binary component, you'll need to ensure that a binary
wheel is available for the platform you're targeting. For desktop platforms,
binary wheels are hosted on `PyPI <https://pypi.org>`__; Android binary wheels
are hosted on the `Chaquopy package index <https://chaquo.com/pypi-7.0/>`__; iOS
binary wheels are available on the `BeeWare repository on anaconda.org
<https://anaconda.org/beeware/repo>`__.

The Android and iOS repositories do not have binary wheels for *every* package
that is on PyPI. If you experience problems when building or running an app on a
mobile platform that appear to be related to a missing dependency, check the
build logs for your app. If you see:

* On Android: the error `"Chaquopy cannot compile native code"
  <https://chaquo.com/chaquopy/doc/current/faq.html#chaquopy-cannot-compile-native-code>`__
* On iOS: the error "Cannot compile native modules"
* A reference to downloading a ``.tar.gz`` version of the package
* A reference to ``Building wheels for collected packages: <package>``

The binary dependency isn't supported on mobile. Binary mobile packages are
currently maintained by the BeeWare team; if you have a particular third-party
package that you'd like us to support, `open a ticket
<https://github.com/beeware/briefcase>`__ providing details.
