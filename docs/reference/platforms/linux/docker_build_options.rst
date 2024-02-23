``--Xdocker-build=<value>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A configuration argument to be passed to the Docker build command for the app
image. For example, to provide an additional build argument to the Dockerfile,
specify ``--Xdocker-build=--build-arg=ARG=value``. See `the Docker build
documentation
<https://docs.docker.com/engine/reference/commandline/image_build/#options>`__
for details on the full list of options that can be provided.

You may specify multiple ``--Xdocker-build`` arguments; each one specifies a
single argument to pass to Docker, in the order they are specified.
