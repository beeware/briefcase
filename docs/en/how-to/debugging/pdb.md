# Debug via PDB   { #debug-pdb }

It is possible to debug a Briefcase app via [PDB](https://docs.python.org/3/library/pdb.html) at different stages in your development process. You can debug a development app via `briefcase dev`, but also a bundled app that is built via `briefcase build` and run via `briefcase run`.

## Development

Debugging a development app is quite easy. Just add `breakpoint()` inside your code and start the app via `briefcase dev`. When the breakpoint is hit, the PDB console opens in your terminal and you can debug your app.

## Bundled App

It is also possible to debug a bundled app. This is currently still an **experimental feature** that is only supported on Windows, macOS and iOS.

To debug a bundled app, at first you have to add `breakpoint()` somewhere in your code, where the debugger should halt.

Then you have to built your app with the debugger embedded into your app. This is done via:

```console
$ briefcase build --debug pdb
```

This will build your app in debug mode and add [`remote-pdb`](https://pypi.org/project/remote-pdb/) together with a package that automatically starts `remote-pdb` on startup of your bundled app.

Then it is time to run your app. You can do this via:

```console
$ briefcase run --debug pdb
```

Running the app in debug mode will automatically start the `remote-pdb` debugger and wait for incoming connections. By default, it will listen on `localhost` and port `5678`.

In a separate terminal on your host system, connect to your bundled app:

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

To connect to your application, you need access to `telnet`. That is not activated by default, but can be activated by running the following command with admin rights

```console
$ dism /online /Enable-Feature /FeatureName:TelnetClient
```

Then you can start the connection via

```console
$ telnet localhost 5678
```

///

The app will start after the connection is established.

For more information, see [here][run-debug].
