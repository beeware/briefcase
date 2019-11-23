import enum
import json
import subprocess

from briefcase.exceptions import BriefcaseCommandError


class DeviceState(enum.Enum):
    SHUTDOWN = 0
    BOOTED = 1
    SHUTTING_DOWN = 10
    UNKNOWN = 99


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
            runtime['name'][4:]: runtime['identifier']
            for runtime in simctl_data['runtimes']
            if runtime['name'].startswith('{os_name} '.format(os_name=os_name))
        }

        simulators = {
            version: {
                simulator['udid']: simulator['name']
                for simulator in simctl_data['devices'][identifier]
            }
            for version, identifier in os_versions.items()
        }

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
