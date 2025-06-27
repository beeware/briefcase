==============
Debug your app
==============

If you get stuck when programming your app, it is time to debug your app. The
following sections describe how you can debug your app with or without an IDE.

.. toctree::
   :maxdepth: 1

   console
   vscode


.. _debugging_limitations:

Limitations when debugging bundled apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To debug an bundle app you need an network connection from your host system to
the device your are trying to debug. If your bundled app is also running on
your host system this is no problem. But when debugging a mobile device your
app is running on another device. Running an iOS app in simulator is also no
problem, because the simulator shares the same network stack as your host.
But on Android there is a separate network stack. That's why briefcase will
automatically forward the port from your host to the Android device via ADB.
