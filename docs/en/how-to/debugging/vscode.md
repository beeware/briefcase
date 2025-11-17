# Debug via VS Code   { #debug-vscode }

You can use [Visual Studio Code](https://code.visualstudio.com) to debug a development app via `briefcase dev`, or a bundled app that is built via `briefcase build` and run via `briefcase run` - including mobile apps.

## Development

During development on your host system, you can configure Visual Studio Code to start Briefcase. The "Run" menu in VS Code has an "Open Configurations" option; if that option is enabled, select it, and modify the `configurations` key so that it contains an entry like the following:

```json
{
    ...
    "configurations": [
        ...
        {
            "name": "Briefcase: Dev",
            "type": "debugpy",
            "request": "launch",
            "module": "briefcase",
            "args": [
                "dev",
            ],
            "justMyCode": false
        }
    ]
}
```
If you need to specify other options to `briefcase dev`, you can specify them in the `args` value.

If "Open Configurations" isn't enabled, select "Add Configuration" instead, and then enter the following details:

* Select "Python Debugger" as the debugger
* Select "Module" as the debug configuration
* Enter `briefcase` as the name of the module to run.

This will give you a stub configuration that is mostly correct; edit it to match the example above. The configuration will be saved in a `.vscode/launch.json` file in your project.

To start a debug session, open the debug view in VS Code using the sidebar, select the "Briefcase: Dev" configuration from the list at the top of the sidebar, and select "Start Debugging" from the "Run" menu. This will run `briefcase dev` in a debug session; you can [set breakpoints](https://code.visualstudio.com/docs/debugtest/debugging#_breakpoints), use the [data inspection](https://code.visualstudio.com/docs/debugtest/debugging#_data-inspection), use the [debug console REPL](https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl) and all other debugging features of VS Code. For more details about the VS Code configurations in the `.vscode/launch.json` file, see the [VS Code documentation](https://code.visualstudio.com/docs/python/debugging).

## Bundled App

/// warning | Experimental feature

This is currently an **experimental feature** that is only supported on Windows, macOS and iOS.

///

To debug a bundled app, the app must be modified to include a bootstrap that will connect to the VS Code debugger. This is done by passing the `--debug debugpy` option to `briefcase build`:

```console
$ briefcase build --debug debugpy
```

To build a mobile app, include the platform name in the `build` command - for example:

```console
$ briefcase build iOS --debug debugpy
```

This will build your app in debug mode and add [debugpy](https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl), and a package that automatically starts `debugpy` at the startup of your bundled app.

Then, select "Open Configurations" from the "Run" menu, and add a new debug configuration to your `.vscode/launch.json` file:

```json
{
    "version": "0.2.0",
    "configurations": [
        ...
        {
            "name": "Briefcase: Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "justMyCode": false
        }
    ]
}
```

You can now start your app in debug mode:

```console
$ briefcase run --debug debugpy
```

To run a mobile app, include the platform name in the `run` command - for example:

```console
$ briefcase run iOS --debug debugpy
```

Running the app in debug mode will automatically start the `debugpy` debugger and listen for incoming connections. By default it will listen on `localhost` and port `5678`. The app will pause at the start of execution, waiting for the debugger to attach.

To attach the debugger, select the Debug sidebar, select the "Briefcase: Attach" configuration, and then select "Start Debugging" from the "Run" menu. The app will then resume, and the debugger will be enabled. You can then use any debugger features you require.

## Debugging quirks

The VS Code debugger has some notable behavior when used to debug a Briefcase app:

- The "Restart" debug control will not work. To restart the app, you need to disconnect the debugger, restart the app manually, running it with `briefcase run --debug debugpy`, and then re-connecting the debugger.
- `justMyCode` must be set to `false`. When setting it to `true`, or not defining it at all, breakpoints are missed on some platforms (e.g., Windows). The reason for this is currently unknown.
- `pathMappings` should not be set manually in the `launch.json`. The path mappings will be set by Briefcase programmatically and if setting it manually too the manual setting will overwrite settings by Briefcase.
- VS Code will not honor any breakpoint in code that is part of a file that is ignored by `.gitignore`.
