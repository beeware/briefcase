import enum
import json
import re
import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError


class DeviceState(enum.Enum):
    SHUTDOWN = 0
    BOOTED = 1
    SHUTTING_DOWN = 10
    UNKNOWN = 99


def verify_command_line_tools_install(command):
    """Verify that command line developer tools are installed and ready for use.

    A completely clean machine will have neither Xcode *or* the Command Line
    Tools. However, it's possible to install Xcode and *not* install the command
    line tools, and vice versa.

    Lastly, there is a license that needs to be accepted.

    :param command: The command that needs to perform the verification check.
    """
    ensure_command_line_tools_are_installed(command)
    confirm_xcode_license_accepted(command)


def verify_xcode_install(command, min_version=None):
    """Verify that Xcode and the command line developer tools are installed and
    ready for use.

    We need Xcode, *and* the Xcode Command Line Tools. A completely clean
    machine will have neither Xcode *or* the Command Line Tools. However,
    it's possible to install Xcode and *not* install the command line tools,
    and vice versa.

    We also need to ensure that an adequate version of Xcode is available.

    Then, there is a license that needs to be accepted.

    Lastly, we ensure that the iOS simulator is installed.

    :param command: The command that needs to perform the verification check.
    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    """
    ensure_xcode_is_installed(command, min_version=min_version)
    ensure_command_line_tools_are_installed(command)
    confirm_xcode_license_accepted(command)


def ensure_command_line_tools_are_installed(command):
    """
    Determine if the Xcode command line tools are installed.

    If they are not installed, an exception is raised; in addition, a OS dialog
    will be displayed prompting the user to install Xcode.

    :param command: The command that needs to perform the verification check.
    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
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
        command.subprocess.check_output(
            ['xcode-select', '--install'],
            stderr=subprocess.STDOUT
        )
        raise BriefcaseCommandError("""
Xcode command line developer tools are not installed.

You should be shown a dialog prompting you to install Xcode and the
command line tools. Select "Install" to install the command line developer
tools.

Re-run Briefcase once that installation is complete.
""")
    except subprocess.CalledProcessError as e:
        if e.returncode != 1:
            print("""
*************************************************************************
** WARNING: Unable to determine if Xcode is installed                  **
*************************************************************************

   Briefcase will proceed, assuming everything is OK. If you experience
   problems, this is almost certainly the cause of those problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/new

   In your report, please including the output from running:

     xcode-select --install

   from the command prompt.

*************************************************************************
""")


def ensure_xcode_is_installed(
    command,
    xcode_location=None,
    min_version=None,
):
    """
    Determine if Xcode is installed; and if so, that it meets minimum version
    requirements.

    Raises an exception if XCode isn't installed, or if the version of Xcode
    that is installed doesn't meet the minimum requirement.

    :param command: The command that needs to perform the verification check.
    :param xcode_location: The location where Xcode should be installed.
        If not given, the location returned by `xcode-select -p` will be used.
    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    """
    # Try the direct approach. Look for the Xcode folder that is created
    # when you install from the App store.

    if xcode_location is None:

        try:
            output = command.subprocess.check_output(
                ['xcode-select', '-p'],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            xcode_location = output.strip()
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError("""
Could not find Xcode installation.

To select an existing Xcode installation, run:

    $ sudo xcode-select --switch path/to/Xcode.app

or install Xcode from the macOS App Store. Re-run Briefcase afterwards.
""")

    if not Path(xcode_location).exists():
        raise BriefcaseCommandError("""
Xcode is not installed.

You can install Xcode from the macOS App Store.

Re-run Briefcase once that installation is complete.
""")

    try:
        output = command.subprocess.check_output(
            ['xcodebuild', '-version'],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        if min_version is not None:
            if output.startswith('Xcode '):
                try:
                    # Split content up to the first \n
                    # then split the content after the first space
                    # and split that content on the dots.
                    # Append 0's to fill any gaps caused by
                    # version numbers that don't have a minor version.
                    version = tuple(
                        int(v)
                        for v in output.split('\n')[0].split(' ')[1].split('.')
                    ) + (0, 0)

                    if version < min_version:
                        raise BriefcaseCommandError(
                            "Xcode {min_version} is required; {version} is installed. Please update Xcode.".format(
                                min_version='.'.join(str(v) for v in min_version),
                                version='.'.join(str(v) for v in version),
                            )
                        )
                    else:
                        # Version number is acceptable
                        return
                except IndexError:
                    pass

            print("""
*************************************************************************
** WARNING: Unable to determine the version of Xcode that is installed **
*************************************************************************

   Briefcase will proceed, assuming everything is OK. If you experience
   problems, this is almost certainly the cause of those problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/new

   In your report, please including the output from running:

     xcodebuild -version

   from the command prompt.

*************************************************************************
""")

    except subprocess.CalledProcessError as e:
        if " is a command line tools instance" in e.output:
            raise BriefcaseCommandError("""
Xcode may be installed, but the active developer directory is a
command line tools instance. To make the default Xcode install the
active developer directory, run:

    $ sudo xcode-select --switch /Applications/Xcode.app

Or, to use a version of Xcode installed in a non-default location:

    $ sudo xcode-select --switch /path/to/Xcode.app

and then re-run Briefcase.
""")
        else:
            raise BriefcaseCommandError("""
The Xcode install appears to exist, but Briefcase was unable to
determine the current Xcode version. Running:

    $ xcodebuild -version

should return the current Xcode version, but it raised an error.

You may need to re-install Xcode. Re-run Briefcase once that
installation is complete.
""")


def confirm_xcode_license_accepted(command):
    """
    Confirm if the Xcode license has been accepted.

    :param command: The command that needs to perform the verification check.
    """
    # Lastly, check if the XCode license has been accepted. The command line
    # tools return a status code of 69 (nice...) if the license has not been
    # accepted. In this case, we can prompt the user to accept the license.
    try:
        command.subprocess.check_output(
            ['/usr/bin/clang', '--version'],
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 69:
            print("""
Use of Xcode and the iOS developer tools are covered by a license that must be
accepted before you can use those tools.

You can accept these licenses by starting Xcode and clicking "Accept"; or, you
can run:

    $ sudo xcodebuild -license

at the command line and accepting the license there.

Briefcase will try the command line version of this command now. You will need
to enter your password (Briefcase will not store this password anywhere).
""")
            try:
                command.subprocess.run(
                    ['sudo', 'xcodebuild', '-license'],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                # status code 1 - sudo fail
                # status code 69 - license not accepted.
                if e.returncode == 1:
                    raise BriefcaseCommandError("""
Briefcase was unable to run the Xcode licensing tool. This may be because you
did not enter your password correctly, or because your account does not have
administrator priviliges on this computer.

You need to accept the Xcode license before Briefcase can package your app.
""")
                elif e.returncode == 69:
                    raise BriefcaseCommandError("""
Xcode license has not been accepted. Briefcase cannot continue.

You need to accept the Xcode license before Briefcase can package your app.
""")
                else:
                    print("""
*************************************************************************
** WARNING: Unable to determine if the Xcode license has been accepted **
*************************************************************************

   Briefcase will proceed, assuming everything is OK. If you experience
   problems, this is almost certainly the cause of those problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/new

   In your report, please including the output from running:

     sudo xcodebuild -license

   from the command prompt.

*************************************************************************
""")
        else:
            print("""
*************************************************************************
** WARNING: Unable to determine if the Xcode license has been accepted **
*************************************************************************

   Briefcase will proceed, assuming everything is OK. If you experience
   problems, this is almost certainly the cause of those problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/new

   In your report, please including the output from running:

     /usr/bin/clang --version

   from the command prompt.

*************************************************************************
""")


def get_simulators(
    command,
    os_name,
    simulator_location='/Library/Developer/PrivateFrameworks/CoreSimulator.framework/',
):
    """
    Obtain the simulators available on this machine.

    The return value is a 2 level dictionary. The outer dictionary is
    keyed by OS version; the inner dictionary for each OS version
    contains the details of the available simulators, keyed by UDID.

    :param command: The command that needs to know the list of available
        simulators.
    :param os_name: The OS that we want to simulate.
        One of `"iOS"`, `"watchOS"`, or `"tvOS"`.
    :param simulator_location: The filesystem path where the simulator
        frameworks are installed.
    :returns: A dictionary of available simulators.
    """
    # If the simulator frameworks don't exist, they will be downloaded
    # and installed. This should only occur on first execution.
    if not Path(simulator_location).exists():
        command.input("""
It looks like the {os_name} Simulator is not installed. The {os_name} Simulator
must be installed with administrator priviliges.

xcodebuild will prompt you for your admin password so that it can download
and install the simulator.

Press Return to continue: """.format(os_name=os_name))

    try:
        simctl_data = json.loads(
            command.subprocess.check_output(
                ['xcrun', 'simctl', 'list', '-j'],
                universal_newlines=True
            )
        )

        os_versions = {
            runtime['name']: runtime['identifier']
            for runtime in simctl_data['runtimes']
            if runtime['name'].startswith('{os_name} '.format(os_name=os_name))
            and runtime['isAvailable']
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
                device['udid']: device['name']
                for device in simctl_data['devices'].get(
                    identifier,
                    simctl_data['devices'].get(version, [])
                )
                if device['isAvailable']
            }
            for version, identifier in os_versions.items()
        }

        # Purge any versions with no devices
        versions_with_no_devices = [
            version
            for version, devices in simulators.items()
            if len(devices) == 0
        ]
        for version in versions_with_no_devices:
            simulators.pop(version)

        return simulators

    except subprocess.CalledProcessError:
        raise BriefcaseCommandError(
            "Unable to run xcrun simctl."
        )


def get_device_state(command, udid):
    """
    Determine the state of an iOS simulator device.

    :param command: The command that needs to know the simulator device state.
    :param udid: The UDID of the device to inspect
    :returns: The status of the device, as a DeviceState enum.
    """
    try:
        simctl_data = json.loads(
            command.subprocess.check_output(
                ['xcrun', 'simctl', 'list', 'devices', '-j', udid],
                universal_newlines=True
            )
        )

        for runtime, devices in simctl_data['devices'].items():
            for device in devices:
                if device['udid'] == udid:
                    return {
                        'Booted': DeviceState.BOOTED,
                        'Shutting Down': DeviceState.SHUTTING_DOWN,
                        'Shutdown': DeviceState.SHUTDOWN,
                    }.get(device['state'], DeviceState.UNKNOWN)

        # If we fall out the bottom of the loop, the UDID didn't match
        # so we raise an error.
        raise BriefcaseCommandError(
            "Unable to determine status of device {udid}.".format(
                udid=udid
            )
        )
    except subprocess.CalledProcessError:
        raise BriefcaseCommandError(
            "Unable to run xcrun simctl."
        )


# A regex pattern that matches the content returned by `security find-identity`
IDENTITY_RE = re.compile(r'\s*\d+\) ([0-9A-F]{40}) \"(.*)\"')


def get_identities(command, policy):
    """
    Obtain a set of valid identities for the given policy

    :param command: The command that needs the identities.
    :param policy: The identity policy to evaluate (e.g., ``codesigning``)
    """
    try:
        output = command.subprocess.check_output(
            ['security', 'find-identity', '-v', '-p', policy],
            universal_newlines=True
        )

        identities = dict(
            IDENTITY_RE.match(line).groups()
            for line in output.split('\n')
            if IDENTITY_RE.match(line)
        )

        return identities
    except subprocess.CalledProcessError:
        raise BriefcaseCommandError(
            "Unable to run xcrun simctl."
        )
