Inconsistent content in non-universal wheels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When building a universal app (i.e., an app that supports both arm64 and x86_64) that
uses binary wheels, Briefcase will look for ``universal2`` multi-architecture wheels by
default. However, if such a wheel is not available, Briefcase will download a
platform-specific wheel for each platform, and then attempt to merge them into a single
binary.

For most wheels, this approach works without difficulty. However, the wheels for some
packages include slightly different content on each platform. NumPy is a notable example
- it includes static libraries (``.a`` files), headers (``.h`` files), and a
``__config__.py`` file that records the configuration options that were used at the time
the wheel was built.

These files cannot be merged, as they either contain fundamentally inconsistent content,
or are in a binary format that doesn't allow for multi-architecture merging.

Briefcase will warn when it finds files that cannot be merged, and will fall back to
copying the version matching the platform where Briefcase has been executed (i.e., if
you're running on an arm64 MacBook, the version from the arm64 wheel will be copied). You
must determine whether this will cause a problem at runtime.

For many forms of content, the files that cannot be merged are **not** used at
runtime. For example, the ``.a`` and ``.h`` files provided by NumPy exist so that code
can statically link against NumPy. They are not needed at runtime by Python code that
imports and uses NumPy.

If you determine that content is not needed at runtime, it can be removed from the app
using the ``cleanup_paths`` configuration option::

    cleanup_paths = [
        "**/app_packages/**/*.a",
        "**/app_packages/**/*.h",
    ]

This will find and purge all ``.a`` content and ``.h`` content in your app's
dependencies. You can add additional patterns to remove other unneeded content.
