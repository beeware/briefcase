===============================
Briefcase configuration options
===============================

Environment variables
=====================

``BRIEFCASE_HOME``
~~~~~~~~~~~~~~~~~~

When briefcase runs, it will download the support files, tools, and SDKs
necessary to support building and packaging apps. By default, it will store the
files in a platform-native cache folder:

* macOS: ``~/Library/Caches/org.beeware.briefcase``
* Windows: ``%LOCALAPPDATA%\BeeWare\briefcase\Cache``
* Linux: ``~/.cache/briefcase``

If you want to use a different folder to store the Briefcase resources, you can
define a ``BRIEFCASE_HOME`` environment variable.

There are three restrictions on this path specification:

1. The path must already exist. If it doesn't exist, you should create it manually.
2. It *must not* contain any spaces.
3. It *must not* be on a network drive.

The second two restrictions both exist because some of the tools that Briefcase
uses (in particular, the Android SDK) do not work in these locations.
