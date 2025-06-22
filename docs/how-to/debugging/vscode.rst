================
Debug via VSCode
================

Debugging is possible at different stages in your development process. It is
different to debug a development app via ``briefcase dev`` than an bundled app
that is build via ``briefcase build`` and run via ``briefcase run``.

Development
-----------
During development on your host system you should use ``briefcase dev``. To
attach VSCode debugger you can simply create a configuration like this,
that runs ``briefcase dev`` for you and attaches a debugger.

.. code-block:: JSON

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Briefcase: Dev",
                "type": "debugpy",
                "request": "launch",
                "module": "briefcase",
                "args": [
                    "dev",
                ],
                "justMyCode": false
            },
        ]
    }


Bundled App
-----------
It is also possible to debug a bundled app. This is the only way to debug your
app on a mobile device (iOS/Android). Note that there are some :ref:`limitations <debugging_limitations>`
when debugging an bundled app.

For this you need to embed a remote debugger into your app. This is done via:

.. code-block:: console

    $ briefcase build --debug debugpy

This will build your app in debug mode and add the `debugpy <https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl>`_ together with a
package that automatically starts ``debugpy`` at the startup of your bundled app.
Additionally it will optimize the app for debugging. This means e.g. that all
``.py`` files are accessible on the device.

Then it is time to run your app. You can do this via:

.. code-block:: console

    $ briefcase run --debug debugpy

Running the app in debug mode will automatically start the ``debugpy`` debugger
and listen for incoming connections. By default it will listen on ``localhost``
and port ``5678``. You can then connect your VSCode debugger to the app by
creating a configuration like this in the ``launch.json`` file:

.. code-block:: JSON

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Briefcase: Attach",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost",
                    "port": 5678
                }
            }
        ]
    }

The app will not start until you attach the debugger. Once you attached the
VSCode debugger you are ready to debug your app. You can set `breakpoints <https://code.visualstudio.com/docs/debugtest/debugging#_breakpoints>`_
, use the `data inspection <https://code.visualstudio.com/docs/debugtest/debugging#_data-inspection>`_
, use the `debug console REPL <https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl>`_
and all other debugging features of VSCode :)
