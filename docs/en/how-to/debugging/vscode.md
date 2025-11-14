# Debug via VS Code   { #debug-vscode }

Debugging is possible at different stages in your development process. You can debug a development app via `briefcase dev`, or a bundled app that is built via `briefcase build` and run via `briefcase run`.

## Development

During development on your host system you should use `briefcase dev`. To attach the VS Code debugger you have to create a configuration in your `.vscode/launch.json` file like this:

```json
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

To start a debug session, open the debug view in VS Code using the sidebar, select the "Briefcase: Dev" configuration and press `Start Debugging (F5)`. That will run `briefcase dev` in a debug session.

For more details about the VS Code configurations in the `.vscode/launch.json` file see the [VS Code documentation](https://code.visualstudio.com/docs/python/debugging).

## Bundled App

It is also possible to debug a bundled app. This is currently still an **experimental feature** that is only supported on Windows, macOS and iOS.

To debug a bundled app a piece of the debugger has to be embedded into your app. This is done via:

```console
$ briefcase build --debug debugpy
```

This will build your app in debug mode and add [debugpy](https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl) together with a package that automatically starts `debugpy` at the startup of your bundled app.

Then it is time to run your app. You can do this via:

```console
$ briefcase run --debug debugpy
```

Running the app in debug mode will automatically start the `debugpy` debugger and listen for incoming connections. By default it will listen on `localhost` and port `5678`. You can then connect your VS Code debugger to the app by creating a configuration like this in the `.vscode/launch.json` file:

```json
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
            },
            "justMyCode": false
        }
    ]
}
```

The app will not start until you attach the debugger. Once you attach the VS Code debugger, you can set [breakpoints](https://code.visualstudio.com/docs/debugtest/debugging#_breakpoints), use the [data inspection](https://code.visualstudio.com/docs/debugtest/debugging#_data-inspection), use the [debug console REPL](https://code.visualstudio.com/docs/debugtest/debugging#_debug-console-repl) and all other debugging features of VS Code.

But there are some restrictions that must be taken into account:

- Restarting your application via the green circle is not working. You have to stop the app manually and start it again via `briefcase run --debug debugpy`.
- `justMyCode` has to be set to `false`. When setting it to `true`, or not defining it at all, breakpoints are missed on some platforms (e.g., Windows). The reason for this is currently unknown.
- `pathMappings` should not be set manually in the `launch.json`. The path mappings will be set by Briefcase programmatically and if setting it manually too the manual setting will overwrite settings by Briefcase.

For more information see [here][run-debug].
