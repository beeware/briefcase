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
It is also possible to debug a bundled app. This is currently still an **experimental feature** that is only
supported on Windows and macOS. The full power of this feature will become available when iOS and
Android are supported, because that is the only way to debug an iOS or Android app.

To debug a bundled app a piece of the debugger has to be embedded into your app. This is done via:

.. code-block:: console

    $ briefcase build --debug debugpy

This will build your app in debug mode and add `debugpy <https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl>`_ together with a
package that automatically starts ``debugpy`` at the startup of your bundled app.

Then it is time to run your app. You can do this via:

.. code-block:: console

    $ briefcase run --debug debugpy

Running the app in debug mode will automatically start the ``debugpy`` debugger
and listen for incoming connections. By default it will listen on ``localhost``
and port ``5678``. You can then connect your VSCode debugger to the app by
creating a configuration like this in the ``.vscode/launch.json`` file:

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
                "justMyCode": false
            }
        ]
    }

The app will not start until you attach the debugger. Once you attached the
VSCode debugger you are ready to debug your app. You can set `breakpoints <https://code.visualstudio.com/docs/debugtest/debugging#_breakpoints>`_
, use the `data inspection <https://code.visualstudio.com/docs/debugtest/debugging#_data-inspection>`_
, use the `debug console REPL <https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl>`_
and all other debugging features of VSCode 🙂

But there are some restrictions, that must be taken into account:

- Restart the debugger via the green circle is not working correctly.
- ``justMyCode`` has to be set to ``false``. An incorrect configuration can disrupt debugging support.
- ``pathMappings`` should not be set manually. This will be set by briefcase dynamically. An incorrect configuration can disrupt debugging support.
