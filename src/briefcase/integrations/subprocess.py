from __future__ import annotations

import contextlib
import json
import operator
import os
import queue
import shlex
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from functools import wraps
from pathlib import Path
from subprocess import CompletedProcess
from typing import TypeVar, Union

import psutil

from briefcase.config import AppConfig
from briefcase.console import Log
from briefcase.exceptions import CommandOutputParseError, ParseError
from briefcase.integrations.base import Tool, ToolCache

SubprocessArgT = Union[str, Path]
SubprocessArgsT = Sequence[SubprocessArgT]
JsonT = Union[Mapping[str, "JsonT"], Sequence["JsonT"], str, int, float, bool, None]
ParserOutputT = TypeVar("ParserOutputT")


class StopStreaming(Exception):
    """Raised by streaming filters to terminate the stream."""


def ensure_str(text: str | bytes) -> str:
    """Returns input text as a string."""
    return text.decode() if isinstance(text, bytes) else str(text)


def json_parser(json_output: str) -> JsonT:
    """Wrapper to parse command output as JSON via parse_output.

    :param json_output: command output to parse as JSON
    """
    try:
        return json.loads(json_output)
    except json.JSONDecodeError as e:
        raise ParseError(f"Failed to parse output as JSON: {e}") from e


def is_process_dead(pid: int) -> bool:
    """Returns True if a PID is not assigned to a process.

    Checking if a PID exists is only a semi-safe proxy to determine if a process is dead
    since PIDs can be re-used. Therefore, this function should only be used via constant
    monitoring of a PID to identify when the process goes from existing to not existing.

    :param pid: integer value to be checked if assigned as a PID.
    :returns: True if PID does not exist; False otherwise.
    """
    return not psutil.pid_exists(pid)


def get_process_id_by_command(
    command_list: list[str] | None = None,
    command: str = "",
    logger: Log | None = None,
) -> int | None:
    """Find a Process ID (PID) a by its command. If multiple processes are found, then
    the most recently created process ID is returned.

    :param command_list: list of a command's fully qualified path and its arguments.
    :param command: a partial or complete fully-qualified filepath to a command.
        This is primarily intended for use on macOS where the `open` command
        takes a filepath to a directory for an application; therefore, the actual
        running process will be running a command within that directory.
    :param logger: optional Log to show messages about process matching to users
    :returns: PID if found else None
    """
    matching_procs = []
    # retrieve command line, creation time, and ID for all running processes.
    # note: psutil returns None for a process attribute if it is unavailable;
    #   this is most likely to happen for restricted or zombie processes.
    for proc in psutil.process_iter(["cmdline", "create_time", "pid"]):
        proc_cmdline: list[str] = proc.info["cmdline"]
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
    def inner(sub: Subprocess, args: SubprocessArgsT, *wrapped_args, **wrapped_kwargs):
        """Evaluate whether conditions are met to remove any dynamic elements in the
        console before returning control to Subprocess.

        :param sub: Bound Subprocess object
        :param args: command line to run in subprocess
        :returns: the return value for the Subprocess method
        """
        # Just run the command if no dynamic elements are active
        if not sub.tools.input.is_console_controlled:
            return sub_method(sub, args, *wrapped_args, **wrapped_kwargs)

        remove_dynamic_elements = False

        # Batch (.bat) scripts on Windows.
        # If cmd.exe is interrupted with CTRL+C while running a bat script,
        # it may prompt the user to abort the script and dynamic elements
        # such as the Wait Bar can hide this message from the user.
        if sub.tools.host_os == "Windows":
            executable = str(args[0]).strip() if args else ""
            remove_dynamic_elements |= executable.lower().endswith(".bat")

        # Release control for commands that cannot be streamed.
        remove_dynamic_elements |= wrapped_kwargs.get("stream_output") is False

        # Run subprocess command with or without console control
        if remove_dynamic_elements:
            with sub.tools.input.release_console_control():
                return sub_method(sub, args, *wrapped_args, **wrapped_kwargs)
        else:
            return sub_method(sub, args, *wrapped_args, **wrapped_kwargs)

    return inner


class PopenOutputStreamer(threading.Thread):
    def __init__(
        self,
        label: str,
        popen_process: subprocess.Popen,
        logger: Log,
        capture_output: bool = False,
        filter_func: Callable[[str], Iterator[str]] | None = None,
    ):
        """Thread for streaming stdout for a Popen process.

        :param label: Descriptive name for process being streamed
        :param popen_process: Popen process with stdout to stream
        :param logger: logger for printing to console
        :param capture_output: Retain process output in ``output_queue`` via a
            ``queue.Queue`` instead of printing to console
        :param filter_func: a callable that will be invoked on every line of output
            that is streamed; see ``Subprocess.stream_output`` for details
        """
        super().__init__(name=f"{label} output streamer", daemon=True)

        self.popen_process = popen_process
        self.logger = logger
        self.capture_output = capture_output
        self.filter_func = filter_func

        # arbitrarily large maxsize to prevent unbounded memory use if things go south
        self.output_queue = queue.Queue(maxsize=10_000_000)
        self.stop_flag = threading.Event()

    def run(self):
        """Stream output for a Popen process."""
        try:
            while output_line := self._readline():
                # The stop_flag is intentionally checked both at the top and bottom of
                # this loop; if the flag was set during the call to readline(), then
                # processing the output is skipped altogether. And if the flag is set
                # as a consequence of filter_func(), the streamer still exits before
                # calling readline() again and potentially blocking indefinitely.
                if not self.stop_flag.is_set():
                    filtered_output, stop_streaming = self._filter(output_line)

                    for filtered_line in filtered_output:
                        if self.capture_output:
                            self.output_queue.put_nowait(filtered_line)
                        else:
                            self.logger.info(filtered_line)

                    if stop_streaming:
                        self.stop_flag.set()

                if self.stop_flag.is_set():
                    break
        except Exception as e:
            self.logger.error(f"Error while streaming output: {type(e).__name__}: {e}")
            self.logger.capture_stacktrace("Output thread")

    def request_stop(self):
        """Set the stop flag to cause the streamer to exit.

        If the streamer is currently blocking on `readline()` because the process'
        stdout buffer is empty, then the streamer will not exit until `readline()`
        returns or until Briefcase exits.
        """
        self.stop_flag.set()

    @property
    def captured_output(self) -> str:
        """The captured output from the process."""
        output = []
        while not self.output_queue.empty():
            with contextlib.suppress(queue.Empty):
                output.append(self.output_queue.get_nowait())
                self.output_queue.task_done()
        return "".join(output)

    def _readline(self) -> str:
        """Read a line of output from the process while blocking.

        Calling readline() for stdout always returns at least a newline, i.e. "\n",
        UNLESS the process is exiting or already exited; in that case, an empty string
        is returned.

        :returns: one line of output or "" if nothing more can be read from stdout
        """
        try:
            return ensure_str(self.popen_process.stdout.readline())
        except ValueError as e:
            # Catch ValueError if stdout is unexpectedly closed; this can
            # happen, for instance, if the user starts spamming CTRL+C.
            if "I/O operation on closed file" in str(e):
                self.logger.warning(
                    "WARNING: stdout was unexpectedly closed while streaming output"
                )
                return ""
            else:
                raise

    def _filter(self, line: str) -> tuple[list[str], bool]:
        """Run filter function over output from process."""
        filtered_output = []
        stop_streaming = False

        if self.filter_func is not None:
            try:
                for filtered_line in self.filter_func(line.strip("\n")):
                    filtered_output.append(filtered_line)
            except StopStreaming:
                stop_streaming = True
        else:
            filtered_output.append(line)

        return filtered_output, stop_streaming


class NativeAppContext(Tool):
    """A wrapper around subprocess for use as an app-bound tool."""

    name = "app_context_subprocess"

    @classmethod
    def verify_install(cls, tools: ToolCache, app: AppConfig, **kwargs) -> Subprocess:
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
        super().__init__(tools=tools)
        self._subprocess = subprocess

    def prepare(self):
        """Perform any environment preparation required to execute processes."""
        # This is a no-op; the native subprocess environment is ready-to-use.
        pass

    @contextlib.contextmanager
    def run_app_context(self, subprocess_kwargs: dict[str, ...]) -> dict[str, ...]:
        """A manager to wrap subprocess calls to run a Briefcase project app.

        :param subprocess_kwargs: initialized keyword arguments for subprocess calls
        """
        # This is a no-op; the native subprocess environment is ready-to-use.
        yield subprocess_kwargs

    def full_env(self, overrides: dict[str, str | None] | None) -> dict[str, str]:
        """Generate the full environment in which the command will run.

        If an env var in `overrides` is set to `None`, then that env var
        will be altogether absent in the returned environment.

        :param overrides: The environment passed to the subprocess call;
            can be `None` if there are no explicit environment changes.
        """
        env = self.tools.os.environ.copy()
        if overrides:
            env.update(overrides)
            env = {k: v for k, v in env.items() if v is not None}
        return env

    def final_kwargs(self, **kwargs) -> dict[str, str]:
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

        # Default to running subprocess in "text" mode so all output is returned as
        # strings instead of bytes. The legacy setting of `universal_newlines` is
        # converted to `text` for calling subprocess.
        kwargs["text"] = kwargs.pop("universal_newlines", kwargs.get("text", True))

        # Enable text mode if an `encoding` or `errors` is specified; this aligns with
        # the default behavior of subprocess.
        kwargs["text"] |= any(kwargs.get(kw) for kw in ["encoding", "errors"])

        # Configure subprocess for text mode
        if kwargs["text"]:
            # Ensure an appropriate encoding is specified.
            # If an encoding isn't provided, default to the encoding that Python is
            # using for stdout. This is for the benefit of Windows which uses cp437 for
            # console output when the system encoding is cp1252.
            # `sys.__stdout__` is used because Rich captures and redirects `sys.stdout`.
            # The fallback to "UTF-8" is needed to catch the case where stdout is
            # redirected to a non-tty (e.g. during pytest conditions).
            kwargs.setdefault(
                "encoding", os.device_encoding(sys.__stdout__.fileno()) or "UTF-8"
            )

            # Use relaxed output decoding by default.
            # subprocess defaults to "strict" handling for errors arising from decoding
            # output to Unicode. To avoid Unicode exceptions from misbehaving commands,
            # set `errors` so output that cannot be decoded for the specified encoding
            # are replaced with hex of the raw bytes.
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
    def verify_install(cls, tools: ToolCache, **kwargs) -> Subprocess:
        """Make subprocess available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "subprocess"):
            return tools.subprocess

        tools.subprocess = Subprocess(tools=tools)
        return tools.subprocess

    @ensure_console_is_safe
    def run(
        self,
        args: SubprocessArgsT,
        stream_output: bool = True,
        filter_func: Callable[[str], Iterator[str]] | None = None,
        **kwargs,
    ) -> CompletedProcess:
        """A wrapper for subprocess.run().

        This method implements the behavior of subprocess.run() with some notable
        differences:

          - The command's output is streamed if ``stream_output=True`` or if dynamic
            console content such as the Wait Bar is active and I/O is not redirected.
          - If dynamic content is not active, ``stream_output=False`` will disable
            streaming.
          - If the ``env`` argument is provided, the current system environment will be
            copied, and the contents of env overwritten into that environment.
          - The ``text`` argument is defaulted to True so all output is returned as
            strings instead of bytes.

        Output Streaming Primer
        ~~~~~~~~~~~~~~~~~~~~~~~

        What is output streaming?
        -------------------------

        When a command is invoked via ``subprocess.run()``, by default, its stdout and
        stderr are connected directly to the console and the output is presented to the
        user as though the command was invoked natively. When output streaming is
        active, Briefcase reads the command's output and prints it in to the console on
        behalf of the command.

        Why is output streaming necessary?
        ----------------------------------

        Allowing commands to print directly to the console can provide superior UX since
        it allows tools to provide their native experience to users.

        However, a primary mechanism for providing support for Briefcase is asking users
        to provide the log file when errors occur. Often, these errors are raised by
        invoked commands; streaming the output of commands allows Briefcase to capture
        that output and include it in the log file as well as the console.

        Additionally, the content of the console can become corrupted if other processes
        print to the console while Rich's dynamic console elements such as a Progress
        Bar are active. Streaming such output allows Rich to maintain integrity of all
        the console content.

        How does output streaming work?
        -------------------------------

        Streaming is activated when:

          1. dynamic content such as the Wait Bar is active and I/O is not redirected

          2. the ``stream_output`` argument is ``True`` (as it is by default)

        I/O is considered redirected when both ``stdout`` and ``stderr`` are specified
        (e.g., when ``stdout`` and ``stderr`` are set to``subprocess.PIPE`` so the
        output is available to the caller).

        To facilitate streaming the output, ``stdout`` is set to ``subprocess.PIPE``. If
        ``stderr`` is not specified by calling code, then it is set to
        ``subprocess.STDOUT`` so it is interlaced with stdout output.

        The process is created for the command with ``Popen``, and a separate thread is
        started for continuously reading and printing the stdout to the console from the
        command process. It is necessary to read from stdout in a thread because the
        read is uninterruptible; so, a user may not be able to abort with CTRL-C.

        When the process ends (or the user sends CTRL-C), a call is made to ensure the
        command process terminates; this, in turn, ensures the thread for streaming can
        properly exit its otherwise infinite loop. The calling code is either returned a
        ``CompletedProcess`` object or ``CalledProcessError`` could be raised.

        Output streaming ultimately strives to simulate calling ``subprocess.run()``
        while proxying the command's output to the console.

        When *not* to use output streaming?
        -----------------------------------

        When streaming is disabled, the command's output **WILL NOT** be included the
        Briefcase log file. This makes troubleshooting difficult and should be avoided.
        However, there are some situations where disabling streaming is unavoidable.

        Some commands use their own dynamic console content such as progress bars,
        spinners, and other animations. When such output is streamed, its quality can be
        significantly compromised and look terrible in the console for users. If it is
        not possible to disable such output with e.g. a flag for the command, then
        disabling streaming may be necessary. As an example, the ``flatpak install``
        command uses many animations.

        If a command requires user input, do not use output streaming. The output
        streaming implementation doesn't provide any facilities to send input to the
        process and doesn't provide any special handling of stdin. Additionally, when
        the command process prompts the user for input, that doesn't always trigger
        ``readline()`` to return; so, the console may actually end up waiting for user
        input before displaying a prompt to the user. As an example, accepting Android
        SDK licenses requires user input.

        :param args: args for ``subprocess.run()``
        :param stream_output: simulate ``run()`` while streaming the output to the
            console. Set to False if the command requires user interaction.
        :param filter_func: If output streaming is enabled, a callable that will be
            invoked on every line of output that is streamed. The function accepts the
            "raw" line of input (stripped of any trailing newline); it returns a
            generator that yields the filtered output that should be displayed to the
            user. Can raise StopStreaming to terminate the output stream.
        :param kwargs: keyword args for ``subprocess.run()``
        :raises ValueError: if a filter function is provided when in non-streaming mode.
        :returns: ``CompletedProcess`` for invoked process
        """

        # Stream the output unless the caller explicitly disables it. When a
        # caller sets stream_output=False, then ensure_console_is_safe() will
        # disable any dynamic console elements while the command runs.
        if stream_output:
            return self._run_and_stream_output(args, filter_func=filter_func, **kwargs)

        # Can't filter non-streamed output.
        if filter_func:
            raise ValueError("Cannot apply a filter to non-streamed output.")

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

    def _run_and_stream_output(
        self,
        args: SubprocessArgsT,
        check: bool = False,
        filter_func: Callable[[str], Iterator[str]] | None = None,
        **kwargs,
    ) -> CompletedProcess:
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
            self.stream_output(args[0], process, filter_func=filter_func)
            if process.stderr and kwargs["stderr"] != subprocess.STDOUT:
                stderr = process.stderr.read()
        return_code = process.poll()
        self._log_return_code(return_code)

        if check and return_code:
            raise subprocess.CalledProcessError(return_code, args, stderr=stderr)

        return subprocess.CompletedProcess(args, return_code, stderr=stderr)

    @ensure_console_is_safe
    def check_output(self, args: SubprocessArgsT, quiet: bool = False, **kwargs) -> str:
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

        :param args: commands and its arguments to run via subprocess
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

    def parse_output(
        self,
        output_parser: Callable[[str], ParserOutputT],
        args: SubprocessArgsT,
        **kwargs,
    ) -> ParserOutputT:
        """A wrapper for check_output() where the command output is processed through
        the supplied parser function.

        If the parser fails, CommandOutputParseError is raised. The parsing function
        should take one string argument and should raise ParseError for failure modes.

        :param output_parser: a function that takes str input and returns parsed
            content, or raises ParseError in the case of a parsing problem.
        :param args: The arguments to pass to the subprocess
        :param kwargs: The keyword arguments to pass to the subprocess
        :returns: Parsed data read from the subprocess output; the exact structure of
            that data is dependent on the output parser used.
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

    def Popen(self, args: SubprocessArgsT, **kwargs) -> subprocess.Popen:
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
        label: str,
        popen_process: subprocess.Popen,
        stop_func: Callable[[], bool] = lambda: False,
        filter_func: Callable[[str], Iterator[str]] | None = None,
    ):
        """Stream the output of a Popen process until the process exits. If the user
        sends CTRL+C, the process will be terminated.

        This is useful for starting a process via Popen such as tailing a log file, then
        initiating a non-blocking process that populates that log, and finally streaming
        the original process's output here.

        :param label: A description of the content being streamed; used for to provide
            context in logging messages.
        :param popen_process: a running Popen process with output to print
        :param stop_func: A Callable that returns True when output streaming should stop
            and the popen_process should be terminated.
        :param filter_func: A callable that will be invoked on every line of output that
            is streamed. The function accepts the "raw" line of input (stripped of any
            trailing newline); it returns a generator that yields the filtered output
            that should be displayed to the user. Can raise StopStreaming to terminate
            the output stream.
        """
        output_streamer = PopenOutputStreamer(
            label=label,
            popen_process=popen_process,
            logger=self.tools.logger,
            filter_func=filter_func,
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

    def stream_output_non_blocking(
        self,
        label: str,
        popen_process: Popen,
        capture_output: bool = False,
        filter_func: Callable[[str], Iterator[str]] | None = None,
    ) -> PopenOutputStreamer:
        """Stream the output of a Popen process without blocking.

        This is useful for streaming or capturing the output of a process in the
        background. In this way, the process' output can be shown to users while the
        main thread monitors other activities; alternatively, the output of the process
        can be captured to be retrieved later in the event of an error, for instance.

        :param label: A description of the content being streamed; used for to provide
            context in logging messages.
        :param popen_process: A running Popen process with output to print
        :param capture_output: Retain process output instead of printing to the console
        :param filter_func: A callable that will be invoked on every line of output that
            is streamed. The function accepts the "raw" line of input (stripped of any
            trailing newline); it returns a generator that yields the filtered output
            that should be displayed to the user. Can raise StopStreaming to terminate
            the output stream.
        """
        output_streamer = PopenOutputStreamer(
            label=label,
            popen_process=popen_process,
            logger=self.tools.logger,
            capture_output=capture_output,
            filter_func=filter_func,
        )
        output_streamer.start()
        return output_streamer

    def cleanup(self, label: str, popen_process: subprocess.Popen):
        """Clean up after a Popen process, gracefully terminating if possible; forcibly
        if not.

        :param label: A description of the content being streamed; used for to provide
            context in logging messages.
        :param popen_process: The Popen instance to clean up.
        """
        popen_process.terminate()
        try:
            popen_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.tools.logger.warning(f"Forcibly killing {label}...")
            popen_process.kill()

    def _log(self, msg: str = ""):
        """Funnel for all subprocess details logging."""
        self.tools.logger.debug(msg, preface=">>> " if msg else "")

    def _log_command(self, args: SubprocessArgsT):
        """Log the entire console command being executed."""
        self._log()
        self._log("Running Command:")
        self._log(f"    {' '.join(shlex.quote(str(arg)) for arg in args)}")

    def _log_cwd(self, cwd: str | Path | None):
        """Log the working directory for the command being executed."""
        effective_cwd = Path.cwd() if cwd is None else cwd
        self._log("Working Directory:")
        self._log(f"    {effective_cwd}")

    def _log_environment(self, overrides: dict[str, str] | None):
        """Log the environment variables overrides prior to command execution.

        :param overrides: The explicit environment passed to the subprocess call;
            can be `None` if there are no explicit environment changes.
        """
        if overrides:
            self._log("Environment Overrides:")
            for env_var, value in overrides.items():
                self._log(f"    {env_var}={value}")

    def _log_output(self, output: str, stderr: str | None = None):
        """Log the output of the executed command."""
        if output:
            self._log("Command Output:")
            for line in ensure_str(output).splitlines():
                self._log(f"    {line}")

        if stderr:
            self._log("Command Error Output (stderr):")
            for line in ensure_str(stderr).splitlines():
                self._log(f"    {line}")

    def _log_return_code(self, return_code: int | str):
        """Log the output value of the executed command."""
        self._log(f"Return code: {return_code}")
