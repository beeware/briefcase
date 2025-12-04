# Debug via PDB   { #debug-pdb }

You can use [PDB](https://docs.python.org/3/library/pdb.html) to debug a development app via `briefcase dev`, or a bundled app that is built via `briefcase build` and run via `briefcase run` - including mobile apps.

## Development

To debug an app in development mode, add `breakpoint()` to your code somewhere that will be executed, and start the app with `briefcase dev`. When the breakpoint is reached, the PDB console will open in your terminal and you can debug your app.

## Bundled App

/// warning | Note

This is currently an **experimental feature** that is only supported on Windows, macOS and iOS.

///

To debug a bundled app, add `breakpoint()` somewhere in your code where the debugger should halt.

Your app must then be modified to include a bootstrap that will connect to the VS Code debugger. This is done by passing the `--debug pdb` option to `briefcase build`:

```console
$ briefcase build --debug pdb
```

To build a mobile app, include the platform name in the `build` command - for example:

```console
$ briefcase build iOS --debug pdb
```

This will build your app in debug mode, adding [`remote-pdb`](https://pypi.org/project/remote-pdb/), and a package that automatically starts `remote-pdb` on startup of your bundled app.

You can then run your app in debug mode:

```console
$ briefcase run --debug pdb
```

To run a mobile app, include the platform name in the `run` command - for example:

```console
$ briefcase run iOS --debug pdb
```

Running the app in debug mode will automatically start the `remote-pdb` debugger and wait for incoming connections. By default, it will listen on `localhost` and port `5678`. In a separate terminal on your host system, connect to your bundled app:

/// tab | macOS

```console
$ nc localhost 5678
```

///

/// tab | Linux

```console
$ nc localhost 5678
```

///

/// tab | Windows

To connect to your application, you need access to `telnet`. `telnet` is not enabled by default; it can be activated by running the following command with admin rights:

```console
$ dism /online /Enable-Feature /FeatureName:TelnetClient
```

You can then start the connection with:

```console
$ telnet localhost 5678
```

///

The app will start after the connection is established. When a breakpoint is reached, the PDB prompt will be displayed, allowing you to interact with the app.
