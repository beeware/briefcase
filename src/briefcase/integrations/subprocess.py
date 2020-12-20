import shlex
import subprocess


class Subprocess:
    """
    A wrapper around subprocess that can be used as a logging point for
    commands that are executed.
    """
    def __init__(self, command):
        self.command = command
        self._subprocess = subprocess

    def prepare(self):
        """
        Perform any environment preparation required to execute processes.
        """
        # This is a no-op; the native subprocess environment is ready-to-use.
        pass

    def final_kwargs(self, **kwargs):
        """Convert subprocess keyword arguments into their final form.
        """
        # If `env` has been provided, inject a full copy of the local
        # environment, with the values in `env` overriding the local
        # environment.
        try:
            extra_env = kwargs.pop('env')
            kwargs['env'] = self.command.os.environ.copy()
            kwargs['env'].update(extra_env)
        except KeyError:
            # No explicit environment provided.
            pass

        # If `cwd` has been provded, ensure it is in string form.
        try:
            cwd = kwargs.pop('cwd')
            kwargs['cwd'] = str(cwd)
        except KeyError:
            pass

        return kwargs

    def run(self, args, **kwargs):
        """A wrapper for subprocess.run()

        If verbosity >= 2, the executed command will be printed to the console.

        The behavior of this method is identical to subprocess.run(),
        except for the `env` argument. If provided, the current system
        environment will be copied, and the contents of env overwritten
        into that environment.
        """
        # Invoke subprocess.run().
        # Pass through all arguments as-is.
        # All exceptions are propegated back to the caller.
        if self.command.verbosity >= 2:
            print(">>> {cmdline}".format(
                cmdline=' '.join(shlex.quote(str(arg)) for arg in args)
            ))

        return self._subprocess.run(
            [
                str(arg) for arg in args
            ],
            **self.final_kwargs(**kwargs)
        )

    def check_output(self, args, **kwargs):
        """A wrapper for subprocess.check_output()

        If verbosity >= 2, the executed command will be printed to the console.

        The behavior of this method is identical to subprocess.check_output(),
        except for the `env` argument. If provided, the current system
        environment will be copied, and the contents of env overwritten
        into that environment.
        """
        # Invoke subprocess.check_output
        if self.command.verbosity >= 2:
            print(">>> {cmdline}".format(
                cmdline=' '.join(shlex.quote(arg) for arg in args)
            ))

        return self._subprocess.check_output(
            [
                str(arg) for arg in args
            ],
            **self.final_kwargs(**kwargs)
        )

    def Popen(self, args, **kwargs):
        """A wrapper for subprocess.Popen()

        If verbosity >= 2, the executed command will be printed to the console.

        The behavior of this method is identical to subprocess.Popen(),
        except for the `env` argument. If provided, the current system
        environment will be copied, and the contents of env overwritten
        into that environment.
        """
        # Invoke subprocess.check_output
        if self.command.verbosity >= 2:
            print(">>> {cmdline}".format(
                cmdline=' '.join(shlex.quote(arg) for arg in args)
            ))

        return self._subprocess.Popen(
            [
                str(arg) for arg in args
            ],
            **self.final_kwargs(**kwargs)
        )
