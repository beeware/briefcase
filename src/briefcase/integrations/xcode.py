import enum
import re
import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, CommandOutputParseError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import json_parser


class DeviceState(enum.Enum):
    SHUTDOWN = 0
    BOOTED = 1
    SHUTTING_DOWN = 10
    UNKNOWN = 99


def verify_xcode_install(tools: ToolCache, min_version: tuple = None):
    """Verify that Xcode and the command line developer tools are installed and ready
    for use.

    We need Xcode, *and* the Xcode Command Line Tools. A completely clean
    machine will have neither Xcode *nor* the Command Line Tools. However,
    it's possible to install Xcode and *not* install the command line tools,
    and vice versa.

    We also need to ensure that an adequate version of Xcode is available.

    Then, there is a license that needs to be accepted.

    Lastly, we ensure that the iOS simulator is installed.

    :param tools: ToolCache of available tools
    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    """
    # short circuit since already verified and available
    if hasattr(tools, "xcode"):
        return

    ensure_xcode_is_installed(tools, min_version=min_version)
    verify_command_line_tools_install(tools)
    tools.xcode = True


def verify_command_line_tools_install(tools: ToolCache):
    """Verify that command line developer tools are installed and ready for use.

    A completely clean machine will have neither Xcode *nor* the Command Line
    Tools. However, it's possible to install Xcode and *not* install the command
    line tools, and vice versa.

    Lastly, there is a license that needs to be accepted.

    :param tools: ToolCache of available tools
    """
    # short circuit since already verified and available
    if hasattr(tools, "xcode_cli"):
        return

    ensure_command_line_tools_are_installed(tools)
    confirm_xcode_license_accepted(tools)
    tools.xcode_cli = True


def ensure_command_line_tools_are_installed(tools: ToolCache):
    """Determine if the Xcode command line tools are installed.

    If they are not installed, an exception is raised; in addition, an OS dialog
    will be displayed prompting the user to install Xcode.

    :param tools: ToolCache of available tools
    """
    # We determine if the command line tools are installed by running:
    #
    #   xcode-select --install
    #
    # If that command exits with status 0, it means the tools are *not*
    # installed; but a dialog will be displayed prompting an installation.
    #
    # If it returns a status code of 1, the tools are already installed
    # and outputs the message "command line tools are already installed"
    #
    # Any other status code is a problem.
    try:
        tools.subprocess.check_output(["xcode-select", "--install"])
        raise BriefcaseCommandError(
            """\
The command line developer tools are not installed.

You should be shown a dialog prompting you to install them. Select "Install"
to continue, and re-run Briefcase once that installation is complete.
"""
        )
    except subprocess.CalledProcessError as e:
        if e.returncode != 1:
            tools.logger.warning(
                """
*************************************************************************
** WARNING: Unable to determine if Xcode is installed                  **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you experience
    problems, this is almost certainly the cause of those problems.

    Please report this as a bug at:

       https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

        $ xcode-select --install

    from the command prompt.

*************************************************************************
"""
            )


def ensure_xcode_is_installed(
    tools: ToolCache,
    min_version: tuple = None,
    xcode_location="/Applications/Xcode.app",
):
    """Determine if Xcode is installed; and if so, that it meets minimum version
    requirements.

    Raises an exception if XCode isn't installed, or if the version of Xcode
    that is installed doesn't meet the minimum requirement.

    :param tools: ToolCache of available tools
    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    :param xcode_location: The location where we expect to find an Xcode install.
        Used for testing; defaults to ``/Applications/Xcode.app``.
    """
    # Check for *any* version of Xcode tools. xcode-select returns:
    #  * The path to the currently active Xcode install; or
    #  * error code 2 - No Xcode installation
    try:
        tools.subprocess.check_output(["xcode-select", "-p"])
    except subprocess.CalledProcessError as e:
        raise BriefcaseCommandError(
            """\
Could not find an Xcode installation.

To select an existing Xcode installation, run:

    $ sudo xcode-select --switch path/to/Xcode.app

or install Xcode from the macOS App Store. Once you have installed Xcode,
you can re-run Briefcase.
"""
        ) from e

    try:
        # xcodebuild -version returns the version of Xcode that is currently
        # selected. If the current Xcode is a commandline tools install,
        # returns an error:
        #   xcode-select: error: tool 'xcodebuild' requires Xcode, but active
        #   developer directory '/Library/Developer/CommandLineTools' is a
        #   command line tools instance
        output = tools.subprocess.check_output(["xcodebuild", "-version"])

        if min_version is not None:
            # Look for a line in the output that reads "Xcode X.Y.Z"
            version_lines = [
                line for line in output.split("\n") if line.startswith("Xcode ")
            ]
            if version_lines:
                # Split the content after the first space
                # and split that content on the dots.
                # Append 0's to fill any gaps caused by
                # version numbers that don't have a minor version.
                # At this point, version lines *must* have at least one element,
                # and each line *must* have a string with at least one space,
                # so if either array lookup fails, something weird is happening.
                version = tuple(
                    int(v) for v in version_lines[0].split(" ")[1].split(".")
                ) + (0, 0)

                if version < min_version:
                    min_version = ".".join(str(v) for v in min_version)
                    version = ".".join(str(v) for v in version)
                    raise BriefcaseCommandError(
                        f"Xcode {min_version} is required; {version} is installed. Please update Xcode."
                    )
                else:
                    # Version number is acceptable
                    return

            tools.logger.warning(
                """
*************************************************************************
** WARNING: Unable to determine the version of Xcode that is installed **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you experience
    problems, this is almost certainly the cause of those problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

        $ xcodebuild -version

    from the command prompt.

*************************************************************************
"""
            )

    except subprocess.CalledProcessError as e:
        if " is a command line tools instance" in e.output:
            # Commandline tools are currently selected. Look for the existence
            # of the default folder; if that folder doesn't exist, we can't
            # conclude that Xcode *isn't* installed.
            if Path(xcode_location).exists():
                preamble = """\
Xcode appears to be installed, but the active developer directory is the Xcode
command line tools. To make Xcode the active developer directory, run:

    $ sudo xcode-select --switch /Applications/Xcode.app
"""
            else:
                preamble = """\
You have the Xcode command line tools installed; however, Briefcase requires
a full Xcode install. Xcode can be downloaded from the macOS App Store at
<https://apps.apple.com/au/app/xcode/id497799835?mt=12>.
"""

            raise BriefcaseCommandError(
                preamble
                + """
Or, to use a version of Xcode installed in a non-default location:

    $ sudo xcode-select --switch /path/to/Xcode.app

and then re-run Briefcase.
"""
            ) from e

        else:
            raise BriefcaseCommandError(
                """\
An Xcode install appears to exist, but Briefcase was unable to
determine the current Xcode version. Running:

    $ xcodebuild -version

should return the current Xcode version, but it raised an error.

You may need to re-install Xcode. Re-run Briefcase once that
installation is complete.
"""
            ) from e


def confirm_xcode_license_accepted(tools: ToolCache):
    """Confirm if the Xcode license has been accepted.

    :param tools: ToolCache of available tools
    """
    # Lastly, check if the XCode license has been accepted. The command line
    # tools return a status code of 69 (nice...) if the license has not been
    # accepted. In this case, we can prompt the user to accept the license.
    try:
        tools.subprocess.check_output(["/usr/bin/clang", "--version"])
    except subprocess.CalledProcessError as e:
        if e.returncode == 69:
            tools.logger.info(
                """
Use of Xcode and the iOS developer tools are covered by a license that must be
accepted before you can use those tools.

You can accept these licenses by starting Xcode and clicking "Accept"; or, you
can run this command and accept the license when prompted:

    $ sudo xcodebuild -license

Briefcase will try to run this command now. You will need to enter your
password (Briefcase will not store this password anywhere).
"""
            )
            try:
                tools.subprocess.run(
                    ["sudo", "xcodebuild", "-license"],
                    check=True,
                    stream_output=False,
                )
            except subprocess.CalledProcessError as e:
                # status code 1 - sudo fail
                # status code 69 - license not accepted.
                if e.returncode == 1:
                    raise BriefcaseCommandError(
                        """\
Briefcase was unable to run the Xcode licensing tool. This may be because you
did not enter your password correctly, or because your account does not have
administrator privileges on this computer.

You need to accept the Xcode license before Briefcase can package your app.
"""
                    )
                elif e.returncode == 69:
                    raise BriefcaseCommandError(
                        """\
Xcode license has not been accepted. Briefcase cannot continue.

You need to accept the Xcode license before Briefcase can package your app.
"""
                    )
                else:
                    tools.logger.warning(
                        """
*************************************************************************
** WARNING: Unable to determine if the Xcode license has been accepted **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you experience
    problems, this is almost certainly the cause of those problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

        $ sudo xcodebuild -license

    from the command prompt.

*************************************************************************
"""
                    )
        else:
            tools.logger.warning(
                """
*************************************************************************
** WARNING: Unable to determine if the Xcode license has been accepted **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you experience
    problems, this is almost certainly the cause of those problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

        $ /usr/bin/clang --version

    from the command prompt.

*************************************************************************
"""
            )


def get_simulators(
    tools: ToolCache,
    os_name: str,
    simulator_location="/Library/Developer/PrivateFrameworks/CoreSimulator.framework/",
):
    """Obtain the simulators available on this machine.

    The return value is a 2 level dictionary. The outer dictionary is
    keyed by OS version; the inner dictionary for each OS version
    contains the details of the available simulators, keyed by UDID.

    :param tools: ToolCache of available tools
    :param os_name: The OS that we want to simulate.
        One of `"iOS"`, `"watchOS"`, or `"tvOS"`.
    :param simulator_location: The filesystem path where the simulator
        frameworks are installed.
    :returns: A dictionary of available simulators.
    """
    # If the simulator frameworks don't exist, they will be downloaded
    # and installed. This should only occur on first execution.
    if not Path(simulator_location).exists():
        tools.input(
            f"""
It looks like the {os_name} Simulator is not installed. The {os_name} Simulator
must be installed with administrator privileges.

xcodebuild will prompt you for your admin password so that it can download
and install the simulator.

Press Return to continue: """
        )

    try:
        simctl_data = tools.subprocess.parse_output(
            json_parser,
            ["xcrun", "simctl", "list", "-j"],
        )

        os_versions = {
            runtime["name"]: runtime["identifier"]
            for runtime in simctl_data["runtimes"]
            if runtime["name"].startswith(f"{os_name} ") and runtime["isAvailable"]
        }

        # For some reason, simctl varies the style of key that is used to
        # identify device versions. The first format is OS identifier (e.g.,
        # 'com.apple.CoreSimulator.SimRuntime.iOS-12-0'). The second is a
        # "human readable" name ('iOS 12.0'). We presume (but can't verify)
        # that any given OS version only exists with a single key.
        # SO - Look for an identifier first; then look for the OS name. If
        # neither exist, return an empty list.
        simulators = {
            version: {
                device["udid"]: device["name"]
                for device in simctl_data["devices"].get(
                    identifier, simctl_data["devices"].get(version, [])
                )
                if device["isAvailable"]
            }
            for version, identifier in os_versions.items()
        }

        # Purge any versions with no devices
        versions_with_no_devices = [
            version for version, devices in simulators.items() if len(devices) == 0
        ]
        for version in versions_with_no_devices:
            simulators.pop(version)

        return simulators

    except CommandOutputParseError as e:
        raise BriefcaseCommandError("Unable to parse output of xcrun simctl") from e
    except subprocess.CalledProcessError as e:
        raise BriefcaseCommandError("Unable to run xcrun simctl.") from e


def get_device_state(tools: ToolCache, udid: str):
    """Determine the state of an iOS simulator device.

    :param tools: ToolCache of available tools
    :param udid: The UDID of the device to inspect
    :returns: The status of the device, as a DeviceState enum.
    """
    try:
        simctl_data = tools.subprocess.parse_output(
            json_parser,
            ["xcrun", "simctl", "list", "devices", "-j", udid],
        )

        for runtime, devices in simctl_data["devices"].items():
            for device in devices:
                if device["udid"] == udid:
                    return {
                        "Booted": DeviceState.BOOTED,
                        "Shutting Down": DeviceState.SHUTTING_DOWN,
                        "Shutdown": DeviceState.SHUTDOWN,
                    }.get(device["state"], DeviceState.UNKNOWN)

        # If we fall out the bottom of the loop, the UDID didn't match
        # so we raise an error.
        raise BriefcaseCommandError(f"Unable to determine status of device {udid}.")
    except CommandOutputParseError as e:
        raise BriefcaseCommandError("Unable to parse output of xcrun simctl") from e
    except subprocess.CalledProcessError as e:
        raise BriefcaseCommandError("Unable to run xcrun simctl.") from e


# A regex pattern that matches the content returned by `security find-identity`
IDENTITY_RE = re.compile(r"\s*\d+\) ([0-9A-F]{40}) \"(.*)\"")


def get_identities(tools: ToolCache, policy: str):
    """Obtain a set of valid identities for the given policy.

    :param tools: ToolCache of available tools
    :param policy: The identity policy to evaluate (e.g., ``codesigning``)
    """
    try:
        output = tools.subprocess.check_output(
            ["security", "find-identity", "-v", "-p", policy],
        )

        return dict(
            IDENTITY_RE.match(line).groups()
            for line in output.split("\n")
            if IDENTITY_RE.match(line)
        )

    except subprocess.CalledProcessError as e:
        raise BriefcaseCommandError("Unable to run security find-identity.") from e
