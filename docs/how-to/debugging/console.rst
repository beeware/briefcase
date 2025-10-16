=================
Debug via Console
=================

Debugging an app on the console is normally done via `PDB <https://docs.python.org/3/library/pdb.html>`_.
It is possible to debug a briefcase app at different stages in your development
process. You can debug a development app via ``briefcase dev``, but also an bundled
app that is build via ``briefcase build`` and run via ``briefcase run``.


Development
-----------
Debugging an development app is quiet easy. Just add ``breakpoint()`` inside
your code and start the app via ``briefcase dev``. When the breakpoint got hit
the pdb console opens on your console and you can debug your app.


Bundled App
-----------
It is also possible to debug a bundled app. This is currently still an **experimental feature** that is only
supported on Windows and macOS. The full power of this feature will become available when iOS and
Android are supported, because that is the only way to debug an iOS or Android app.

To debug a bundled app a piece of the debugger has to be embedded into your app. This is done via:

.. code-block:: console

    $ briefcase build --debug pdb

This will build your app in debug mode and add `remote-pdb <https://pypi.org/project/remote-pdb/>`_
together with a package that automatically starts ``remote-pdb`` at the
startup of your bundled app.

Then it is time to run your app. You can do this via:

.. code-block:: console

    $ briefcase run --debug pdb

Running the app in debug mode will automatically start the ``remote-pdb`` debugger
and wait for incoming connections. By default it will listen on ``localhost``
and port ``5678``.

Then it is time to create a new console window on your host system and connect
to your bundled app.

.. tabs::

  .. group-tab:: Windows
    To connect to your application, you need access to ``telnet``. That is not activated by default, but can be
    activated by running the following command with admin rights

    .. code-block:: console

      $ dism /online /Enable-Feature /FeatureName:TelnetClient

    Then you can start the connection via

    .. code-block:: console

      $ telnet localhost 5678

  .. group-tab:: Linux

    .. code-block:: console

      $ nc localhost 5678

  .. group-tab:: macOS

    .. code-block:: console

      $ nc localhost 5678


The app will start after the connection is established.
