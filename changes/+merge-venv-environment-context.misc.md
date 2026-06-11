The ``briefcase.integrations.virtual_environment`` module has been refactored
internally so that ``VenvEnvironment`` is its own context: ``VenvContext`` has
been removed, and its attributes and methods have been merged into
``VenvEnvironment``. The lifecycle work (creating or recreating the venv on
disk) now happens in the constructor of ``VenvEnvironment``, so by the time
``tools.virtual_environment.create(...)`` returns, the venv is ready to use.
The ``with`` block becomes a pure scoping mechanism (``__enter__`` returns
``self`` with no side effects). There is no user-facing behaviour change.
