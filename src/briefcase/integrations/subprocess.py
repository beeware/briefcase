import json
import operator
import os
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

from briefcase.console import Log
from briefcase.exceptions import CommandOutputParseError


class ParseError(Exception):
    """Raised by parser functions to signal parsing was unsuccessful."""


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
    command_list: list = None, command: str = "", logger: Log = None
):
    """Find a Process ID (PID) a by its command. If multiple processes are
    found, then the most recently created process ID is returned.

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


class Subprocess:
    """A wrapper around subprocess that can be used as a logging point for
    commands that are executed."""

    def __init__(self, command):
        self.command = command
        self._subprocess = subprocess

    def prepare(self):
        """Perform any environment preparation required to execute
        processes."""
        # This is a no-op; the native subprocess environment is ready-to-use.
        pass

    def full_env(self, overrides):
        """Generate the full environment in which the command will run.

        :param overrides: The environment passed to the subprocess call;
            can be `None` if there are no explicit environment changes.
        """
        env = self.command.os.environ.copy()
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

        # For Windows, convert start_new_session=True to creation flags
        if self.command.host_os == "Windows":
            try:
                if kwargs.pop("start_new_session") is True:
                    if "creationflags" in kwargs:
                        raise AssertionError(
                            "Subprocess called with creationflags set and start_new_session=True.\n"
                            "This will result in CREATE_NEW_PROCESS_GROUP and CREATE_NO_WINDOW being "
                            "merged in to the creationflags.\n\n"
                            "Ensure this is desired configuration or don't set start_new_session=True."
                        )
                    # CREATE_NEW_PROCESS_GROUP: Makes the new process the root process
                    #     of a new process group. This also disables CTRL+C signal handlers
                    #     for all processes of the new process group.
                    # CREATE_NO_WINDOW: Creates a new console for the process but does not
                    #     open a visible window for that console. This flag is used instead
                    #     of DETACHED_PROCESS since the new process can spawn a new console
                    #     itself (in the absence of one being available) but that console
                    #     creation will also spawn a visible console window.
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

    def run(self, args, stream_output=False, **kwargs):
        """A wrapper for subprocess.run().

        :param args: args for subprocess.run()
        :param stream_output: simulate run() while streaming the output to the console
        :param kwargs: keywords args for subprocess.run()

        The behavior of this method is identical to subprocess.run(),
        except for:
         - If a Wait Bar is active and IO is not redirected, subprocess.run()
           will be simulated so the output can be proxied via stream_output.
         - If the `env` argument is provided, the current system environment
           will be copied, and the contents of env overwritten into that
           environment.
         - The `text` argument is defaulted to True so all output is returned
           as strings instead of bytes.
        """
        # If `stream_output` or dynamic screen content (e.g. a Wait Bar) is
        # active and output is not redirected, use run with output streaming.
        is_output_redirected = kwargs.get("capture_output") or (
            kwargs.get("stdout") and kwargs.get("stderr")
        )
        if stream_output or (
            self.command.input.is_output_controlled and not is_output_redirected
        ):
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

    def check_output(self, args, **kwargs):
        """A wrapper for subprocess.check_output()

        The behavior of this method is identical to
        subprocess.check_output(), except for:
         - If the `env` is argument provided, the current system environment
           will be copied, and the contents of env overwritten into that
           environment.
         - The `text` argument is defaulted to True so all output
           is returned as strings instead of bytes.
        """
        self._log_command(args)
        self._log_cwd(kwargs.get("cwd"))
        self._log_environment(kwargs.get("env"))

        try:
            cmd_output = self._subprocess.check_output(
                [str(arg) for arg in args], **self.final_kwargs(**kwargs)
            )
        except subprocess.CalledProcessError as e:
            self._log_output(e.output, e.stderr)
            self._log_return_code(e.returncode)
            raise

        self._log_output(cmd_output)
        self._log_return_code(0)
        return cmd_output

    def parse_output(self, output_parser, args, **kwargs):
        """A wrapper for check_output() where the command output is processed
        through the supplied parser function.

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
            self.command.logger.error()
            self.command.logger.error("Command Output Parsing Error:")
            self.command.logger.error(f"    {error_reason}")
            self.command.logger.error("Command:")
            self.command.logger.error(
                f"    {' '.join(shlex.quote(str(arg)) for arg in args)}"
            )
            self.command.logger.error("Command Output:")
            for line in ensure_str(cmd_output).splitlines():
                self.command.logger.error(f"    {line}")
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

    def stream_output(self, label, popen_process, stop_func=lambda: False):
        """Stream the output of a Popen process until the process exits. If the
        user sends CTRL+C, the process will be terminated.

        This is useful for starting a process via Popen such as tailing a
        log file, then initiating a non-blocking process that populates that
        log, and finally streaming the original process's output here.

        :param label: A description of the content being streamed; used for
            to provide context in logging messages.
        :param popen_process: a running Popen process with output to print
        :param stop_func: a Callable that returns True when output streaming
            should stop and the popen_process should be terminated.
        """
        output_streamer = threading.Thread(
            name=f"{label} output streamer",
            target=self._stream_output_thread,
            args=(popen_process,),
            daemon=True,
        )
        try:
            output_streamer.start()
            # joining the thread is avoided due to demonstrated
            # instability of thread interruption via CTRL+C (#809)
            while not stop_func() and output_streamer.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.command.logger.info("Stopping...")
            # allow time for CTRL+C to propagate to the child process
            time.sleep(0.25)
        finally:
            self.cleanup(label, popen_process)
            streamer_deadline = time.time() + 3
            while output_streamer.is_alive() and time.time() < streamer_deadline:
                time.sleep(0.1)
            if output_streamer.is_alive():
                self.command.logger.error(
                    "Log stream hasn't terminated; log output may be corrupted."
                )

    def _stream_output_thread(self, popen_process):
        """Stream output for a Popen process in a Thread.

        :param popen_process: popen process to stream stdout
        """
        while True:
            # readline should always return at least a newline (ie \n)
            # UNLESS the underlying process is exiting/gone; then "" is returned
            output_line = ensure_str(popen_process.stdout.readline())
            if output_line:
                self.command.logger.info(output_line)
            elif output_line == "":
                return

    def cleanup(self, label, popen_process):
        """Clean up after a Popen process, gracefully terminating if possible;
        forcibly if not.

        :param label: A description of the content being streamed; used for
            to provide context in logging messages.
        :param popen_process: The Popen instance to clean up.
        """
        popen_process.terminate()
        try:
            popen_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.command.logger.warning(f"Forcibly killing {label}...")
            popen_process.kill()

    def _log_command(self, args):
        """Log the entire console command being executed."""
        self.command.logger.debug()
        self.command.logger.debug("Running Command:")
        self.command.logger.debug(
            f"    {' '.join(shlex.quote(str(arg)) for arg in args)}"
        )

    def _log_cwd(self, cwd):
        """Log the working directory for the  command being executed."""
        effective_cwd = Path.cwd() if cwd is None else cwd
        self.command.logger.debug("Working Directory:")
        self.command.logger.debug(f"    {effective_cwd}")

    def _log_environment(self, overrides):
        """Log the environment variables overrides prior to command execution.

        :param overrides: The explicit environment passed to the subprocess call;
            can be `None` if there are no explicit environment changes.
        """
        if overrides:
            self.command.logger.debug("Environment Overrides:")
            for env_var, value in overrides.items():
                self.command.logger.debug(f"    {env_var}={value}")

    def _log_output(self, output, stderr=None):
        """Log the output of the executed command."""
        if output:
            self.command.logger.debug("Command Output:")
            for line in ensure_str(output).splitlines():
                self.command.logger.debug(f"    {line}")

        if stderr:
            self.command.logger.debug("Command Error Output (stderr):")
            for line in ensure_str(stderr).splitlines():
                self.command.logger.debug(f"    {line}")

    def _log_return_code(self, return_code):
        """Log the output value of the executed command."""
        self.command.logger.debug(f"Return code: {return_code}")
