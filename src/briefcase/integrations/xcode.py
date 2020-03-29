import enum
import json
import re
import subprocess

from briefcase.exceptions import BriefcaseCommandError


class DeviceState(enum.Enum):
    SHUTDOWN = 0
    BOOTED = 1
    SHUTTING_DOWN = 10
    UNKNOWN = 99


def verify_xcode_install(min_version=None, sub=subprocess):
    """Verify that Xcode and the developer tools are installed and ready for use.

    We need Xcode, and the Xcode Command Line Tools. A completely clean
    machine will have neither Xcode *or* the Command Line Tools. However,
    it's possible to install Xcode and *not* install the command line tools.

    We also need to ensure that an adequate version of xcode is available.

    Lastly, there is a license that needs to be accepted.

    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    :param sub: the module for starting subprocesses. Defaults to
        Python's builtin; used for testing purposes.
    """
    ensure_xcode_is_installed(sub=sub)
    check_xcode_version(min_version, sub=sub)
    confirm_xcode_license_accepted(sub=sub)


def ensure_xcode_is_installed(min_version=None, sub=subprocess):
    """
    Determine if Xcode and the command line tools are installed.

    If Xcode is not installed, an exception is raised; in addition, a OS dialog
    will be displayed prompting the user to install Xcode.

    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    :param sub: the module for starting subprocesses. Defaults to
        Python's builtin; used for testing purposes.
    """
    # We determine if Xcode and the command line tools are installed
    # by running:
    #
    #   xcode-select --install
    #
    # If that command exits with status 0, it means Xcode is *not* installed;
    # but a dialog will be displayed prompting the installation of Xcode.
    # If it returns a status code of 1, Xcode is already installed
    # and outputs the message "command line tools are already installed"
    # Any other status code is a problem.
    try:
        sub.check_output(
            ['xcode-select', '--install'],
            stderr=subprocess.STDOUT
        )
        raise BriefcaseCommandError("""
Xcode and the Xcode Command Line tools are not installed.

You should be shown a dialog prompting you to install Xcode and the
command line tools. Select "Get XCode"

Re-run Briefcase once that installation is complete.
""")
    except subprocess.CalledProcessError as e:
        if e.returncode != 1:
            print("""
*************************************************************************
** WARNING: Unable to determine if Xcode is installed                  **
*************************************************************************

   Briefcase will proceed assume everything is OK, but if you
   experience problems, this is almost certainly the cause of those
   problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/

   In your report, please including the output from running:

     xcode-select --install

   from the command prompt.

*************************************************************************
""")


def check_xcode_version(min_version=None, sub=subprocess):
    """
    Determine if the installed version of Xcode meets requirements.

    Raises an exception if the version of Xcode that is installed doesn't
    meet the minimum requirement.

    :param min_version: The minimum allowed version of Xcode, specified as a
        tuple of integers (e.g., (11, 2, 1)). Default: ``None``, meaning there
        is no minimum version.
    :param sub: the module for starting subprocesses. Defaults to
        Python's builtin; used for testing purposes.
    """
    try:
        output = sub.check_output(
            ['xcodebuild', '-version'],
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

   Briefcase will proceed assume everything is OK, but if you
   experience problems, this is almost certainly the cause of those
   problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/

   In your report, please including the output from running:

     xcodebuild -version

   from the command prompt.

*************************************************************************

""")

    except subprocess.CalledProcessError:
        raise BriefcaseCommandError("""
Xcode is not installed.

You can install Xcode from the macOS App Store.
""")


def confirm_xcode_license_accepted(sub=subprocess):
    # Lastly, check if the XCode license has been accepted. The command line
    # tools return a status code of 69 (nice...) if the license has not been
    # accepted. In this case, we can prompt the user to accept the license.
    try:
        sub.check_output(['/usr/bin/clang', '--version'])
    except subprocess.CalledProcessError as e:
        if e.returncode == 69:
            print("""
Use of Xcode and the iOS developer tools are covered by a license that must be
accepted before you can use those tools.

You can accept these licenses by starting Xcode and clicking "Accept"; or, you
can run:

    sudo xcodebuild -license

at the command line and accepting the license there.

Briefcase will try the command line version of this command now. You will need
to enter your password (Briefcase will not store this password anywhere).
""")
            try:
                sub.run(['sudo', 'xcodebuild', '-license'])
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

   Briefcase will proceed assume everything is OK, but if you
   experience problems, this is almost certainly the cause of those
   problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/

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

   Briefcase will proceed assume everything is OK, but if you
   experience problems, this is almost certainly the cause of those
   problems.

   Please report this as a bug at:

     https://github.com/beeware/briefcase/issues/

   In your report, please including the output from running:

     /usr/bin/clang --version

   from the command prompt.

*************************************************************************

""")


def get_simulators(os_name, sub=subprocess):
    """
    Obtain the simulators available on this machine.

    The return value is a 2 level dictionary. The outer dictionary is
    keyed by OS version; the inner dictionary for each OS version
    contains the details of the available simulators, keyed by UDID.

    :param os_name: The OS that we want to simulate.
        One of `"iOS"`, `"watchOS"`, or `"tvOS"`.
    :param sub: the module for starting subprocesses. Defaults to
        Python's builtin; used for testing purposes.
    :returns: A dictionary of available simulators.
    """
    try:
        simctl_data = json.loads(
            sub.check_output(
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


def get_device_state(udid, sub=subprocess):
    """
    Determine the state of an iOS simulator device.

    :param udid: The UDID of the device to inspect
    :param sub: the module for starting subprocesses. Defaults to
        Python's builtin; used for testing purposes.
    :returns: The status of the device, as a DeviceState enum.
    """
    try:
        simctl_data = json.loads(
            sub.check_output(
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


def get_identities(policy, sub=subprocess):
    """
    Obtain a set of valid identities for the given policy

    :param policy: The identity policy to evaluate (e.g., ``codesigning``)
    """
    try:
        output = sub.check_output(
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
