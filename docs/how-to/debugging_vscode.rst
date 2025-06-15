Debugging with VSCode
=====================
Debugging is possible at different stages in your development process. It is
different to debug a development app via `briefcase dev` than an bundled app
that is build via `briefcase build` and run via `briefcase run`.

Development
-----------
During development on your host system you should use `briefcase dev`. To
attach VSCode debugger you can simply create a configuration like this,
that runs `briefcase dev` for you and attaches a debugger.

```
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
```

Bundled App
-----------
It is also possible to debug a bundled app. This is the only way to debug your
app on a mobile device (iOS/Android).

For this you need to embed a remote debugger into your app. This is done via:

```
briefcase build --debug debugpy
```

This will build your app in debug mode and add the `debugpy` package to your
app. Additionally it will optimize the app for debugging. This means e.g. that
all `.py` files are accessible on the device.

Then it is time to run your app. You can do this via:

```
briefcase run --debug debugpy
```

Running the app in debug mode will automatically start the `debugpy` debugger
and listen for incoming connections. By default it will listen on `localhost`
and port `5678`. You can then connect your VSCode debugger to the app by
creating a configuration like this in the `launch.json` file:

```
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

Note, that you need an network connection to the device your are trying to
debug. If your bundled app is running on your host system this is no problem.
But when debugging a mobile device your app is running on another device.
Running an iOS app in simulator is also no problem, because the simulator
shares the same network stack as your host. But on Android there is a separate
network stack. That's why briefcase will automatically forward the port from
your host to the android device via `adb` (Android Debug Bridge).

Now you are ready to debug your app. You can set breakpoints in your code, use
the "Debug Console" and all other debugging features of VSCode :)
