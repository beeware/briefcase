======================
Docker X11 Passthrough
======================

Briefcase can use Docker to build apps for Linux distributions other than the
distribution you're currently using. Docker can also be used to *run* the app
on the foreign distribution, exporting the graphical aspects of the app to your
local display. This document describes how to configure your system to do this.

X Window System Background
--------------------------

Linux distributions use either the `X Window System <https://www.x.org/>`_
(sometimes called X or X11) or `Wayland <https://wayland.freedesktop.org/>`__
to manage their graphical displays. X11 is the older of the two; Wayland
maintains compatibility with the `X11 protocol
<https://www.x.org/releases/X11R7.7/doc/xproto/x11protocol.html>`__ for
backwards compatibility.

The X11 protocol operates in a client/server framework; any application that
wishes to display a window or receive user input will send and receive commands
with an X server.

X Configuration
~~~~~~~~~~~~~~~

The location of the X server is declared by the ``DISPLAY`` environment
variable, normally in the form ``HOSTNAME:DISPLAYNUMBER.SCREENNUMBER``. If
``HOSTNAME`` is absent, it is assumed to be the machine the client is running
on. The ``SCREENNUMBER`` is largely historical since all monitors are normally
collapsed together in to a single screen now. Therefore, an expected setting
for ``DISPLAY`` is ``:0`` for many installations.

While security is relatively weak for X11, there are basic facilities to
mitigate unauthenticated access. The ``XAUTHORITY`` environment variable can
specify a file path to an ``xauth`` database; if ``XAUTHORITY`` is not set,
there will normally be a system default file path configured for each user. The
``xauth`` database itself is protected by file system access controls and
will contain "cookies" for individual displays that are assigned by the X
server for clients to use to facilitate authentication.

An ``xauth`` database authorizing a host named ``jupiter`` might look like:

.. code-block:: console

   $ xauth list
   jupiter/unix:  MIT-MAGIC-COOKIE-1  9e9a67185b1fdc0c46e00dc400559873
   #ffff#6a757069746572#:  MIT-MAGIC-COOKIE-1  9e9a67185b1fdc0c46e00dc400559873

Along with cookie-based authentication, it is also possible to add entities to
an allowlist for a display. For instance, some distributions are configured to
allow any process owned by the logged in user access to the display. This is
configured by ``xhost``.

An ``xhost`` configuration authorizing a user named ``brutus`` might look like:

.. code-block:: console

  $ xhost
  access control enabled, only authorized clients can connect
  SI:localuser:brutus

X Operation
~~~~~~~~~~~

While authentication is normally enabled for X access, security is mostly
bolstered by the allowed methods for clients to connect. Most systems will only
open a UNIX socket to which clients should connect to send and receive
messages. By virtue of file system design, only users on the host machine will
have access to this socket. With the introduction of abstract sockets in Linux,
such a socket is also typically made available in tandem with the UNIX socket.
The advantages of an abstract socket is beyond this discussion, though.

Such a UNIX socket connection will be configured for each display for the
machine. As with many things in Linux, UNIX sockets are exposed in the machine
via a file in the ``/tmp/.X11-unix/`` directory. The socket files are named for
the number of the DISPLAY they are connected to; so, the file for Display 0 is
``X0``. Therefore, any display can be found at ``/tmp/.X11-unix/X#``.

Along with a UNIX socket connection, X servers can also listen on a TCP socket
on the machine's network interfaces. However, since a network connection can
easily be reached by other machines, listening on a TCP socket is normally
disabled on most Linux distributions. That said, the X11 standard reserves port
numbers starting at port 6000 for X displays. Therefore, Display 0 is available
at port 6000 while Display 99 would be available at port 6099 and so on.

Docker
------

From the design of X11, it is clear that a Docker container needs access to the
socket for the display and the ``xauth`` database for the user.

An example of a well-published method to accomplish this:

.. code-block:: console

  $ docker run --rm -it --net host --env DISPLAY ubuntu xeyes

This method assumes:

- the user in the container is ``root`` or its ID matches the host user
- ``xhost`` is configured to allow any connections from the user
- the X server is running an abstract socket for the display

By virtue of how access control is managed for abstract sockets, the
``--net host`` configuration allows access to the abstract socket for the
display inside the container and passing the ``DISPLAY`` environment variable
through lets the ``xeyes`` application know which display to connect to.

While this strategy works in many environments, the generalized solution is
more complicated to accommodate variations in Docker implementations as well as
whether the current display is actually being proxied.

Docker Desktop
~~~~~~~~~~~~~~

The original implementation of Docker is referred to as Docker Engine and
leverages many advanced features of Linux to run processes in highly
containerized environments. Docker Desktop, however, effectively runs Docker
Engine inside a lightweight Linux virtual machine (VM) running on the host
machine. Therefore, when Docker Desktop runs a container, it is running it
inside of a VM and not directly on the host system as Docker Engine does
(albeit in isolation via containerization).

As an outcome of the design of Docker Desktop, the behavior of interactions
between the host machine and Docker containers can be significantly different.
For instance, it is not possible to expose the host machine's network to a
container via ``--net host`` like you can with Docker Engine. While this does
change the exact network configuration that's exposed to the container in the
Docker Desktop VM, it is much different than Docker Engine and abstract sockets
on the host are not available to the container.

Along with not being possible to expose abstract sockets on the host to a
container running via Docker Desktop, it is also not possible to expose
arbitrary UNIX sockets either. Therefore, attempting to bind mount
``/tmp/.X11-unix/X0``, for instance, in to a Docker Desktop container will not
allow processes inside the container to successfully communicate with the
socket. (The Docker team has added support to pass specific sockets such as the
socket Docker itself uses, as well as the SSH agent socket; but exposing
arbitrary sockets has been deemed out of scope for now.)

Therefore, since it is not possible to expose a socket for an X display to a
container running in Docker Desktop, the X display will need to be exposed over
the network shared by the host and container.

Docker Networking
~~~~~~~~~~~~~~~~~

In Docker Engine, networking is relatively straightforward. On the host, a
network interface bridge called ``docker0`` is installed. This bridge serves
to mediate communication among containers as well as between containers and the
host. If the host would like to expose a network-based service to a container,
it can bind to a port on ``docker0`` and containers can connect to it.

In Docker Desktop, however, the Linux VM in which containers run complicates
matters. Inside the Linux VM, it's largely a similar configuration with a
network bridge but the host machine cannot directly interact with this bridge
interface. Instead, the host's network interface is assigned an address on the
bridge similar to how other containers are. In this way, containers can still
connect to network-based services on the host but not through a shared network
interface called ``docker0``.

To help simplify the configurations for applications running inside Docker
Desktop containers, the hostname ``host.docker.internal`` will always resolve
to an IP address for the host's network interface and thereby allow access to
network-based services on the host.

Unlike Docker Desktop, Docker Engine cannot intercept DNS requests from
containers; therefore, ``host.docker.internal`` must be configured when the
container is started. This is accomplished via the ``--add-host`` option which
allows mapping a hostname to an arbitrary address for the hostname. This
mapping is applied by writing it in the container's ``/etc/hosts`` file. Using
``--add-host``, ``host.docker.internal`` is mapped to the keyword
``host-gateway``. This keyword is a special value that the Docker server will
replace with an address from which the host will be reachable within a
container whether it is Docker Engine or Docker Desktop starting it.

In conclusion, we can add ``--add-host host.docker.internal:host-gateway`` to
the options to start a container and the host network interface will be
reachable at ``host.docker.internal``.

Exposing an X Display to a Container
------------------------------------

Given the knowledge of the operation of the Docker implementations, we finally
have the pieces to expose an X display to a container. Since it is not possible
to expose the display's socket directly to a container, a TCP proxy is
configured to pass X messages on the network from the container to the socket
on the host machine for the display.

TCP Proxy
~~~~~~~~~

The `socat <https://repo.or.cz/socat.git>`__ tool is a widely available program
to relay bi-directional data transfer between independent data channels. It
allows running a process on the host to listen on a network port and send any
received data to a socket connected to an X display on the other side.

Creating a TCP proxy for the X display effectively creates a spoofed X display.
The proxy is configured to listen on the TCP port for an unallocated display;
the port number will be 6000 + the number of the display. Additionally, the
proxy is configured to listen on all network interfaces since identifying the
exact interface that will be available within the container is non-trivial.

The other side of the proxy is connected to the socket for the X display. The
socket, though, for the display may actually be another TCP socket; this will
be the case if the environment is currently configured for X11 forwarding over
SSH, as discussed below. In most cases, though, the socket will be the UNIX
socket for the display in the ``/tmp/.X11-unix/`` directory.

X Authentication for the Proxied X Display
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Authentication for X displays is managed in ``xauth`` database files. The
``xauth`` program allows for reading and writing the database. The database is
relatively simple mapping of display information to a cookie. When a client
wants to establish a connection for a display, it queries the database for the
display and receives the cookie back.

Since the proxy creates a spoofed display, a new ``xauth`` database needs to be
created for the spoofed display using the authentication afforded to the user
for the current display.

To create a new database, you need to:

- Extract the cookie for the current display
- Create a new database file
- Add an entry for the spoofed display using the extracted cookie to the new
  database
- Rewrite the hostname of the entry that was just created to be "FamilyWild" (a name
  `reserved by the Xauth specification to match all displays
  <https://www.x.org/archive/current/doc/man/man7/Xsecurity.7.xhtml>`__)

This new ``xauth`` database file is set in the ``XAUTHORITY`` environment
variable for the container so any X connections use it.

The hostname must be updated in the new database file because when the new
entry is created, the ``xauth`` program will associate the host machine's
hostname with the display. In the container, though, the ``DISPLAY`` variable
will be using ``host.docker.internal`` as the hostname for the display. If it
is not updated, then the authentication cannot be used. Furthermore, the
``xauth`` program will not allow creating authentication entries for displays
that do not actually exist. So, we manually update the hostname of the entry to
a wildcard value such that queries for the display number will return the
authentication regardless of the hostname of the query.

X11 Forwarding over SSH
-----------------------

A common practice is to forward X11 communication from a remote machine to the
local machine when using SSH. Therefore, when someone establishes an SSH
connection to another machine and runs Briefcase, this X11 passthrough
mechanism should passthrough the X11 forwarding for SSH in to the Docker
container.

When X11 forwarding is configured for SSH, there are multiple channels
established between the local and remote machine. The primary channel
facilitates the interactive shell session; additionally, though, SSH sets up
another channel for the X communication.

It accomplishes X11 forwarding in much the same way that Briefcase is proxying
X communication from the Docker container to the host. On the remote machine,
the X11 channel is bound to the TCP port for a spoofed display and creates a
new entry in the user's ``xauth`` database for the display. Unlike Briefcase's
proxy, the SSH proxy actively modifies some of the X messages; it will verify
connection attempts use the authentication created in the database by SSH and
will replace it with the actual authentication used on the local machine.

Since Briefcase will first connect to a TCP socket for a display, it will find
the spoofed display created by SSH and create the proxy such that it connects
to that TCP socket. In this way, the container sends X messages to the proxy,
the proxy send them to the SSH X11 channel, and SSH translates them for the X
display on the local machine.
