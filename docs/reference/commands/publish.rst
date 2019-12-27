=======
publish
=======

**COMING SOON**

Uploads your application to a publication channel. By default, targets the
current platform's default output format, using that format's default
publication channel.

You may need to provide additional configuration details (e.g., authentication
credentials), depending on the publication channel selected.

Usage
=====

To publish the application artefacts for the current platform's default output
format to the default publication channel::

    $ briefcase publish

To publish the application artefacts for a different platform::

    $ briefcase publish <platform>

To publish the application artefacts for a specifif output format::

    $ briefcase publish <platform> <output format>

Options
=======

The following options can be provided at the command line.

``-c <channel>`` / ``--channel <channel>``
------------------------------------------

Nominate a publication channel to use.
