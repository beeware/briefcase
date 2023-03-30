import json
import operator
import os
import shlex
import subprocess
import sys
import threading
import time
from functools import wraps
from pathlib import Path

import psutil

from briefcase.config import AppConfig
from briefcase.console import Log
from briefcase.exceptions import CommandOutputParseError, ParseError
from briefcase.integrations.base import Tool, ToolCache


class StopStreaming(Exception):
    """Raised by streaming filters to terminate the stream."""


def ensure_str(text):
    """Returns input text as a string."""
    return text.decode() if isinstance(text, bytes) else str(text)


def json_parser(json_output):
    """Wrapper to parse command output as JSON via parse_output.

    :param json_output: command output to parse as JSON
    """
    try:
        return json.loads(json_output)
    except json.JSONDecodeError as e:
        raise ParseError(f"Failed to parse output as JSON: {e}") from e


def is_process_dead(pid: int):
    """Returns True if a PID is not assigned to a process.

    Checking if a PID exists is only a semi-safe proxy to determine
    if a process is dead since PIDs can be re-used. Therefore, this
    function should only be used via constant monitoring of a PID
    to identify when the process goes from existing to not existing.

    :param pid: integer value to be checked if assigned as a PID.
    :return: True if PID does not exist; False otherwise.
    """
    return not psutil.pid_exists(pid)


def get_process_id_by_command(
    command_list: list = None,
    command: str = "",
    logger: Log = None,
):
    """Find a Process ID (PID) a by its command. If multiple processes are found, then
    the most recently created process ID is returned.

    :param command_list: list of a command's fully qualified path and its arguments.
    :param command: a partial or complete fully-qualified filepath to a command.
        This is primarily intended for use on macOS where the `open` command
        takes a filepath to a directory for an application; therefore, the actual
        running process will be running a command within that directory.
    :param logger: optional Log to show messages about process matching to users
    :return: PID if found else None
    """
    matching_procs = []
    # retrieve command line, creation time, and ID for all running processes.
    # note: psutil returns None for a process attribute if it is unavailable;
    #   this is most likely to happen for restricted or zombie processes.
    for proc in psutil.process_iter(["cmdline", "create_time", "pid"]):
        proc_cmdline = proc.info["cmdline"]
        if command_list and proc_cmdline == command_list:
            matching_procs.append(proc.info)
        if command and proc_cmdline and proc_cmdline[0].startswith(command):
            matching_procs.append(proc.info)

    if len(matching_procs) == 1:
        return matching_procs[0]["pid"]
    elif len(matching_procs) > 1:
        # return the ID of the most recently created matching process
        pid = sorted(matching_procs, key=operator.itemgetter("create_time"))[-1]["pid"]
        if logger:
            logger.info(
                f"Multiple running instances of app found. Using most recently created app process {pid}."
            )
        return pid

    return None


def ensure_console_is_safe(sub_method):
    """Decorator for Subprocess methods to conditionally remove dynamic console elements
    such as the Wait Bar prior to running the subprocess command.

    :param sub_method: wrapped Subprocess method
    """

    @wraps(sub_method)
    def inner(sub, args, **kwargs):
        """Evaluate whether conditions are met to remove any dynamic elements in the
        console before returning control to Subprocess.

        :param sub: Subprocess object
        :param args: list of implicit strings that will be run as subprocess command
        :return: the return value for the Subprocess method
        """
        # Just run the command if no dynamic elements are active
        if not sub.tools.input.is_console_controlled:
            return sub_method(sub, args, **kwargs)

        remove_dynamic_elements = False

        # Batch (.bat) scripts on Windows.
        # If cmd.exe is interrupted with CTRL+C while running a bat script,
        # it may prompt the user to abort the script and dynamic elements
        # such as the Wait Bar can hide this message from the user.
        if sub.tools.host_os == "Windows":
            executable = str(args[0]).strip() if args else ""
            remove_dynamic_elements |= executable.lower().endswith(".bat")

        # Release control for commands that cannot be streamed.
        remove_dynamic_elements |= kwargs.get("stream_output") is False

        # Run subprocess command with or without console control
        if remove_dynamic_elements:
            with sub.tools.input.release_console_control():
                return sub_method(sub, args, **kwargs)
        else:
            return sub_method(sub, args, **kwargs)

    return inner


class NativeAppContext(Tool):
    """A wrapper around subprocess for use as an app-bound tool."""

    @classmethod
    def verify(cls, tools: ToolCache, app: AppConfig):
        """Make subprocess available as app-bound tool."""
        # short circuit since already verified and available
        if hasattr(tools[app], "app_context"):
            return tools[app].app_context

        tools[app].app_context = tools.subprocess
        return tools[app].app_context


class Subprocess(Tool):
    """A wrapper around subprocess that can be used as a logging point for commands that
    are executed."""

    name = "subprocess"
    full_name = "Subprocess"

    def __init__(self, tools: ToolCache):
        self.tools = tools
        self._subprocess = subprocess

    def prepare(self):
        """Perform any environment preparation required to execute processes."""
        # This is a no-op; the native subprocess environment is ready-to-use.
        pass

    def full_env(self, overrides):
        """Generate the full environment in which the command will run.

        :param overrides: The environment passed to the subprocess call;
            can be `None` if there are no explicit environment changes.
        """
        env = self.tools.os.environ.copy()
        if overrides:
            env.update(overrides)
        return env

    def final_kwargs(self, **kwargs):
        """Convert subprocess keyword arguments into their final form.

        This involves:
         * Converting any environment overrides into a full environment
         * Converting the `cwd` into a string
         * Default `text` to True so all outputs are strings
         * Convert start_new_session=True to creationflags on Windows
        """
        # If `env` has been provided, inject a full copy of the local
        # environment, with the values in `env` overriding the local
        # environment.
        try:
            overrides = kwargs.pop("env")
            kwargs["env"] = self.full_env(overrides)
        except KeyError:
            # No explicit environment provided.
            pass

        # If `cwd` has been provided, ensure it is in string form.
        try:
            cwd = kwargs.pop("cwd")
            kwargs["cwd"] = str(cwd)
        except KeyError:
            pass

        # if `text` or backwards-compatible `universal_newlines` are
        # not provided, then default `text` to True so all output is
        # returned as strings instead of bytes.
        if "text" not in kwargs and "universal_newlines" not in kwargs:
            kwargs["text"] = True

        # If we're in text/universal_newlines mode, ensure that there is
        # an encoding specified. If encoding isn't specified, default to
        # the system's stdout encoding.
        # This is for the benefit of Windows, which uses cp437 for console
        # output when the system encoding is cp1252.
        # `__stdout__` is used because rich captures and redirects `sys.stdout`.
        # The fallback to "UTF-8" is needed to catch the case where stdout
        # is redirected to a non-tty (e.g. during pytest conditions)
        if kwargs.get("text") or kwargs.get("universal_newlines", False):
            kwargs.setdefault(
                "encoding", os.device_encoding(sys.__stdout__.fileno()) or "UTF-8"
            )

        # When text mode is enabled, subprocess defaults to "strict"
        # handling for errors arising from decoding output to Unicode.
        # To avoid Unicode exceptions from misbehaving commands, set
        # `errors` so output that cannot be decoded for the specified
        # encoding are replaced with hex of the raw bytes.
        if any(kwargs.get(kw) for kw in ["text", "encoding", "universal_encoding"]):
            kwargs.setdefault("errors", "backslashreplace")

        # For Windows, convert start_new_session=True to creation flags
        if self.tools.host_os == "Windows":
            try:
                if kwargs.pop("start_new_session") is True:
                    if "creationflags" in kwargs:
                        raise AssertionError(
                            "Subprocess called with creationflags set and "
                            "start_new_session=True.\nThis will result in "
                            "CREATE_NEW_PROCESS_GROUP and CREATE_NO_WINDOW "
                            "being merged in to the creationflags.\n\nEnsure "
                            "this is desired configuration or don't set "
                            "start_new_session=True."
                        )
                    # CREATE_NEW_PROCESS_GROUP: Promotes the new process to the root
                    #    process of a new process group. This also disables CTRL+C
                    #    signal handlers for all processes of the new process group.
                    # CREATE_NO_WINDOW: Creates a new console for the process but
                    #    does not open a visible window for that console. This flag
                    #    is used instead of DETACHED_PROCESS since the new process
                    #    can spawn a new console itself (in the absence of one being
                    #    available) but that console creation will also spawn a
                    #    visible console window.
                    new_session_flags = (
                        self._subprocess.CREATE_NEW_PROCESS_GROUP
                        | self._subprocess.CREATE_NO_WINDOW
                    )
                    # merge these flags in to any existing flags already provided
                    kwargs["creationflags"] = (
                        kwargs.get("creationflags", 0) | new_session_flags
                    )
            except KeyError:
                pass

        return kwargs

    @classmethod
    def verify(cls, tools: ToolCache):
        """Make subprocess available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "subprocess"):
            return tools.subprocess

        tools.subprocess = Subprocess(tools)
        return tools.subprocess

    @ensure_console_is_safe
    def run(self, args, stream_output=True, **kwargs):
        """A wrapper for subprocess.run().

        This method implements the behavior of subprocess.run() with some
        notable differences:

          - The command's output is streamed if ``stream_output=True`` or if
            dynamic console content such as the Wait Bar is active and I/O is
            not redirected.
          - If dynamic content is not active, ``stream_output=False`` will
            disable streaming.
          - If the ``env`` argument is provided, the current system environment
            will be copied, and the contents of env overwritten into that
            environment.
          - The ``text`` argument is defaulted to True so all output is returned
            as strings instead of bytes.

        Output Streaming Primer
        ~~~~~~~~~~~~~~~~~~~~~~~

        What is output streaming?
        -------------------------

        When a command is invoked via ``subprocess.run()``, by default, its
        stdout and stderr are connected directly to the console and the output
        is presented to the user as though the command was invoked natively.
        When output streaming is active, Briefcase reads the command's output
        and prints it in to the console on behalf of the command.

        Why is output streaming necessary?
        ----------------------------------

        Allowing commands to print directly to the console can provide superior
        UX since it allows tools to provide their native experience to users.

        However, a primary mechanism for providing support for Briefcase is
        asking users to provide the log file when errors occur. Often, these
        errors are raised by invoked commands; streaming the output of commands
        allows Briefcase to capture that output and include it in the log file
        as well as the console.

        Additionally, the content of the console can become corrupted if other
        processes print to the console while Rich's dynamic console elements
        such as a Progress Bar are active. Streaming such output allows Rich to
        maintain integrity of all the console content.

        How does output streaming work?
        -------------------------------

        Streaming is activated when:

          1. dynamic content such as the Wait Bar is active and I/O is not
             redirected

          2. the ``stream_output`` argument is ``True`` (as it is by default)

        I/O is considered redirected when both ``stdout`` and ``stderr`` are
        specified (e.g., when ``stdout`` and ``stderr`` are set
        to``subprocess.PIPE`` so the output is available to the caller).

        To facilitate streaming the output, ``stdout`` is set to
        ``subprocess.PIPE``. If ``stderr`` is not specified by calling code,
        then it is set to ``subprocess.STDOUT`` so it is interlaced with stdout
        output.

        The process is created for the command with ``Popen``, and a separate
        thread is started for continuously reading and printing the stdout to
        the console from the command process. It is necessary to read from
        stdout in a thread because the read is uninterruptible; so, a user may
        not be able to abort with CTRL-C.

        When the process ends (or the user sends CTRL-C), a call is made to
        ensure the command process terminates; this, in turn, ensures the thread
        for streaming can properly exit its otherwise infinite loop. The calling
        code is either returned a ``CompletedProcess`` object or
        ``CalledProcessError`` could be raised.

        Output streaming ultimately strives to simulate calling
        ``subprocess.run()`` while proxying the command's output to the console.

        When *not* to use output streaming?
        -----------------------------------

        When streaming is disabled, the command's output **WILL NOT** be
        included the Briefcase log file. This makes troubleshooting difficult
        and should be avoided. However, there are some situations where disabling
        streaming is unavoidable.

        Some commands use their own dynamic console content such as progress
        bars, spinners, and other animations. When such output is streamed, its
        quality can be significantly compromised and look terrible in the
        console for users. If it is not possible to disable such output with
        e.g. a flag for the command, then disabling streaming may be necessary.
        As an example, the ``flatpak install`` command uses many animations.

        If a command requires user input, do not use output streaming. The
        output streaming implementation doesn't provide any facilities to send
        input to the process and doesn't provide any special handling of stdin.
        Additionally, when the command process prompts the user for input, that
        doesn't always trigger ``readline()`` to return; so, the console may
        actually end up waiting for user input before displaying a prompt to the
        user. As an example, accepting Android SDK licenses requires user input.

        :param args: args for subprocess.run()
        :param stream_output: simulate run() while streaming the output to the
            console. Set to False if the command requires user interaction.
        :param kwargs: keyword args for subprocess.run()
        :return: `CompletedProcess` for invoked process
        """

        # Stream the output unless the caller explicitly disables it. When a
        # caller sets stream_output=False, then ensure_console_is_safe() will
        # disable any dynamic console elements while the command runs.
        if stream_output:
            return self._run_and_stream_output(args, **kwargs)

        # Otherwise, invoke run() normally.
        self._log_command(args)
        self._log_cwd(kwargs.get("cwd"))
        self._log_environment(kwargs.get("env"))

        try:
            command_result = self._subprocess.run(
                [str(arg) for arg in args], **self.final_kwargs(**kwargs)
            )
        except subprocess.CalledProcessError as e:
            self._log_return_code(e.returncode)
            raise
        self._log_return_code(command_result.returncode)

        return command_result

    def _run_and_stream_output(self, args, check=False, **kwargs):
        """Simulate subprocess.run() while streaming output to the console.

        This is useful when dynamic screen content is active or output should
        be captured for logging.

        When dynamic screen content like a Wait Bar is active, output can
        only be printed to the screen via Log or Console to avoid interfering
        with and likely corrupting the updates to the dynamic screen elements.

        stdout will always be piped so it can be printed to the screen;
        however, stderr can be piped by the caller so it is available
        to the caller in the return value...as with subprocess.run().

        Note: the 'timeout' and 'input' arguments are not supported.
        """
        if kwargs.get("stdout") and not kwargs.get("stderr"):
            # This is an unsupported configuration, as it's not clear where stderr
            # output would be displayed. Either:
            # * Redirect stderr in addition to stdout; or
            # * Use check_output() instead of run() to capture console output
            #   without streaming.
            raise AssertionError(
                "Subprocess.run() was invoked while dynamic Rich content is active (or via "
                "`stream_output`) with stdout redirected while stderr was not redirected."
            )
        for arg in [arg for arg in ["timeout", "input"] if arg in kwargs]:
            raise AssertionError(
                f"The Subprocess.run() '{arg}' argument is not supported "
                f"with `stream_output` or while dynamic Rich content is active."
            )

        # stdout must be piped so the output streamer can print it.
        kwargs["stdout"] = subprocess.PIPE
        # if stderr isn't explicitly redirected, then send it to stdout.
        kwargs.setdefault("stderr", subprocess.STDOUT)
        # use line-buffered output by default
        kwargs.setdefault("bufsize", 1)

        stderr = None
        with self.Popen(args, **kwargs) as process:
            self.stream_output(args[0], process)
            if process.stderr and kwargs["stderr"] != subprocess.STDOUT:
                stderr = process.stderr.read()
        return_code = process.poll()
        self._log_return_code(return_code)

        if check and return_code:
            raise subprocess.CalledProcessError(return_code, args, stderr=stderr)

        return subprocess.CompletedProcess(args, return_code, stderr=stderr)

    @ensure_console_is_safe
    def check_output(self, args, quiet=False, **kwargs):
        """A wrapper for subprocess.check_output()

        The behavior of this method is identical to
        subprocess.check_output(), except for:
         - If the `env` is argument provided, the current system environment
           will be copied, and the contents of env overwritten into that
           environment.
         - The `text` argument is defaulted to True so all output
           is returned as strings instead of bytes.
         - The `stderr` argument is defaulted to `stdout` so _all_ output is
           returned and `stderr` isn't unexpectedly printed to the console.

        :param quiet: Should the invocation of this command be silent, and
            *not* appear in the logs? This should almost always be False;
            however, for some calls (most notably, calls that are called
            frequently to evaluate the status of another process), logging can
            be turned off so that log output isn't corrupted by thousands of
            polling calls.
        """
        # if stderr isn't explicitly redirected, then send it to stdout.
        kwargs.setdefault("stderr", subprocess.STDOUT)

        if not quiet:
            self._log_command(args)
            self._log_cwd(kwargs.get("cwd"))
            self._log_environment(kwargs.get("env"))

        try:
            cmd_output = self._subprocess.check_output(
                [str(arg) for arg in args], **self.final_kwargs(**kwargs)
            )
        except subprocess.CalledProcessError as e:
            if not quiet:
                self._log_output(e.output, e.stderr)
                self._log_return_code(e.returncode)
            raise

        if not quiet:
            self._log_output(cmd_output)
            self._log_return_code(0)
        return cmd_output

    def parse_output(self, output_parser, args, **kwargs):
        """A wrapper for check_output() where the command output is processed through
        the supplied parser function.

        If the parser fails, CommandOutputParseError is raised.
        The parsing function should take one string argument and should
        raise ParseError for failure modes.

        :param output_parser: a function that takes str input and returns
            parsed content, or raises ParseError in the case of a parsing
            problem.
        :param args: The arguments to pass to the subprocess
        :param kwargs: The keyword arguments to pass to the subprocess
        :returns: Parsed data read from the subprocess output; the exact
            structure of that data is dependent on the output parser used.
        """
        cmd_output = self.check_output(args, **kwargs)

        try:
            return output_parser(cmd_output)
        except ParseError as e:
            error_reason = (
                str(e)
                or f"Failed to parse command output using '{output_parser.__name__}'"
            )
            self.tools.logger.error()
            self.tools.logger.error("Command Output Parsing Error:")
            self.tools.logger.error(f"    {error_reason}")
            self.tools.logger.error("Command:")
            self.tools.logger.error(
                f"    {' '.join(shlex.quote(str(arg)) for arg in args)}"
            )
            self.tools.logger.error("Command Output:")
            for line in ensure_str(cmd_output).splitlines():
                self.tools.logger.error(f"    {line}")
            raise CommandOutputParseError(error_reason) from e

    def Popen(self, args, **kwargs):
        """A wrapper for subprocess.Popen()

        The behavior of this method is identical to
        subprocess.check_output(), except for:
         - If the `env` argument is provided, the current system environment
           will be copied, and the contents of env overwritten into that
           environment.
         - The `text` argument is defaulted to True so all output
           is returned as strings instead of bytes.
        """
        self._log_command(args)
        self._log_cwd(kwargs.get("cwd"))
        self._log_environment(kwargs.get("env"))

        return self._subprocess.Popen(
            [str(arg) for arg in args], **self.final_kwargs(**kwargs)
        )

    def stream_output(
        self,
        label,
        popen_process,
        stop_func=lambda: False,
        filter_func=None,
    ):
        """Stream the output of a Popen process until the process exits. If the user
        sends CTRL+C, the process will be terminated.

        This is useful for starting a process via Popen such as tailing a
        log file, then initiating a non-blocking process that populates that
        log, and finally streaming the original process's output here.

        :param label: A description of the content being streamed; used for
            to provide context in logging messages.
        :param popen_process: a running Popen process with output to print
        :param stop_func: a Callable that returns True when output streaming
            should stop and the popen_process should be terminated.
        :param filter_func: a callable that will be invoked on every line
            of output that is streamed. The function accepts the "raw" line
            of input (stripped of any trailing newline); it returns a generator
            that yields the filtered output that should be displayed to the user.
            Can raise StopStreaming to terminate the output stream.
        """
        output_streamer = threading.Thread(
            name=f"{label} output streamer",
            target=self._stream_output_thread,
            args=(popen_process, filter_func),
            daemon=True,
        )
        try:
            output_streamer.start()
            # joining the thread is avoided due to demonstrated
            # instability of thread interruption via CTRL+C (#809)
            while not stop_func() and output_streamer.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.tools.logger.info("Stopping...")
            # allow time for CTRL+C to propagate to the child process
            time.sleep(0.25)
            # re-raise to exit as "Aborted by user"
            raise
        finally:
            self.cleanup(label, popen_process)
            streamer_deadline = time.time() + 3
            while output_streamer.is_alive() and time.time() < streamer_deadline:
                time.sleep(0.1)
            if output_streamer.is_alive():
                self.tools.logger.error(
                    "Log stream hasn't terminated; log output may be corrupted."
                )

    def _stream_output_thread(self, popen_process, filter_func):
        """Stream output for a Popen process in a Thread.

        :param popen_process: popen process to stream stdout
        :param filter_func: a callable that will be invoked on every line
            of output that is streamed; see ``stream_output`` for details.
        """
        try:
            while True:
                try:
                    output_line = ensure_str(popen_process.stdout.readline())
                except ValueError as e:
                    # Catch ValueError if stdout is unexpectedly closed; this can
                    # happen, for instance, if the user starts spamming CTRL+C.
                    if "I/O operation on closed file" in str(e):
                        self.tools.logger.warning(
                            "WARNING: stdout was unexpectedly closed while streaming output"
                        )
                        return
                    else:
                        raise

                # readline should always return at least a newline (ie \n) UNLESS
                # the underlying process is exiting/gone; then "" is returned.
                if output_line:
                    if filter_func:
                        try:
                            for filtered_output in filter_func(
                                output_line.rstrip("\n")
                            ):
                                self.tools.logger.info(filtered_output)
                        except StopStreaming:
                            return
                    else:
                        self.tools.logger.info(output_line)
                else:
                    return
        except Exception as e:
            self.tools.logger.error(
                f"Error while streaming output: {e.__class__.__name__}: {e}"
            )
            self.tools.logger.capture_stacktrace("Output thread")

    def cleanup(self, label, popen_process):
        """Clean up after a Popen process, gracefully terminating if possible; forcibly
        if not.

        :param label: A description of the content being streamed; used for
            to provide context in logging messages.
        :param popen_process: The Popen instance to clean up.
        """
        popen_process.terminate()
        try:
            popen_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.tools.logger.warning(f"Forcibly killing {label}...")
            popen_process.kill()

    def _log_command(self, args):
        """Log the entire console command being executed."""
        self.tools.logger.debug()
        self.tools.logger.debug("Running Command:")
        self.tools.logger.debug(
            f"    {' '.join(shlex.quote(str(arg)) for arg in args)}"
        )

    def _log_cwd(self, cwd):
        """Log the working directory for the  command being executed."""
        effective_cwd = Path.cwd() if cwd is None else cwd
        self.tools.logger.debug("Working Directory:")
        self.tools.logger.debug(f"    {effective_cwd}")

    def _log_environment(self, overrides):
        """Log the environment variables overrides prior to command execution.

        :param overrides: The explicit environment passed to the subprocess call;
            can be `None` if there are no explicit environment changes.
        """
        if overrides:
            self.tools.logger.debug("Environment Overrides:")
            for env_var, value in overrides.items():
                self.tools.logger.debug(f"    {env_var}={value}")

    def _log_output(self, output, stderr=None):
        """Log the output of the executed command."""
        if output:
            self.tools.logger.debug("Command Output:")
            for line in ensure_str(output).splitlines():
                self.tools.logger.debug(f"    {line}")

        if stderr:
            self.tools.logger.debug("Command Error Output (stderr):")
            for line in ensure_str(stderr).splitlines():
                self.tools.logger.debug(f"    {line}")

    def _log_return_code(self, return_code):
        """Log the output value of the executed command."""
        self.tools.logger.debug(f"Return code: {return_code}")
