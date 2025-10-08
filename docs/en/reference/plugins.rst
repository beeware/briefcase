========
Plug-ins
========

Briefcase ships with support for a range of platforms, output formats and GUI toolkits.
Internally, these features are implemented using a plug-in interface; as a result, it is
possible for third-party projects to add their own features to Briefcase by implementing
plug-ins that satisfy those interfaces.

Each plug-in is defined using an `entry point
<https://packaging.python.org/en/latest/specifications/entry-points/>`__ definition in
``pyproject.toml``.

.. _bootstrap-interface:

``briefcase.bootstraps``
========================

The Briefcase :doc:`new project wizard </reference/commands/new>` asks users to select a
GUI toolkit. The option selected at this step alters the content of the code generated
by the wizard, generating framework-specific requirements, system packages, and stub
code for a new application using that GUI framework. These additions are configured
using a ``briefcase.bootstrap`` plug-in.

To add a custom ``briefcase.bootstrap`` plug-in, add a
``[project.entry-points."briefcase.platforms"]`` section to your ``pyproject.toml``
file; each name/value pair under that section will be interpreted as a bootstrap. The
name of each bootstrap setting is the label that will be surfaced to the user in the
wizard. The value is a string identifying a class that implements the
``briefcase.bootstraps.base.BaseGuiBootstrap`` abstract base class.

For example, the Toga bootstrap is implemented using the following configuration::

    [project.entry-points."briefcase.bootstraps"]
    Toga = "briefcase.bootstraps.toga:TogaGuiBootstrap"

``briefcase.platforms`` and ``briefcase.formats.*``
===================================================

Each command implemented by Briefcase is specialized by a platform and output format.
This implementation is defined using a pair of plug-ins - a ``briefcase.platforms``
definition describing a platform, and a ``briefcase.format.<platform>`` definition that
defines the output formats for that platform.

The ``briefcase.platforms`` entry point defines the existence of a platform. Each name
in this section is name of a platform that can be used when invoking Briefcase commands.
The value is a fully-qualified Python module name that must defines a single constant
``DEFAULT_OUTPUT_FORMAT``.

Each platform name is then incorporated into the name of a separate ``format`` entry
point. Each entry in the ``format`` section for a platform is the name of an output
format that can be used when invoking Briefcase commands. The value is a fully-qualified
Python module name that defines 7 symbols:

* ``create`` - a subclass of ``briefcase.commands.create.CreateCommand``
* ``update`` - a subclass of ``briefcase.commands.create.UpdateCommand``
* ``open`` - a subclass of ``briefcase.commands.create.OpenCommand``
* ``build`` - a subclass of ``briefcase.commands.create.BuildCommand``
* ``run`` - a subclass of ``briefcase.commands.create.RunCommand``
* ``package`` - a subclass of ``briefcase.commands.create.PackageCommand``
* ``publish`` - a subclass of ``briefcase.commands.create.PublishCommand``

For example, the definition for the macOS Xcode output format is controlled by the
following::

    [project.entry-points."briefcase.platforms"]
    macOS = "briefcase.platforms.macOS"

    [project.entry-points."briefcase.formats.macOS"]
    xcode = "briefcase.platforms.macOS.xcode"
