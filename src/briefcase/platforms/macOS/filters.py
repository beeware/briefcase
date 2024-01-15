from __future__ import annotations

import re

MACOS_LOG_PREFIX_REGEX = re.compile(
    r"\d{4}-\d{2}-\d{2} (?P<timestamp>\d{2}:\d{2}:\d{2}.\d{3}) Df (.*?)\[.*?:.*?\]"
    r"(?P<subsystem>( \(libffi\.dylib\))|( \(_ctypes\.cpython-3\d{1,2}-.*?\.(so|dylib)\)))? (?P<content>.*)"
)


def macOS_log_clean_filter(line):
    """Filter a macOS system log to extract the Python-generated message content.

    Any system or stub messages are ignored; all logging prefixes are stripped.

    :param line: The raw line from the system log
    :returns: A tuple, containing (a) the log line, stripped of any system
        logging context, and (b) a boolean indicating if the message should be
        included for analysis purposes (i.e., it's Python content, not a system
        message). Returns a single ``None`` if the line should be dumped.
    """
    if any(
        [
            # Log stream outputs the filter when it starts
            line.startswith("Filtering the log data using "),
            # Log stream outputs barely useful column headers on startup
            line.startswith("Timestamp          "),
            # iOS reports an ignorable error on startup
            line.startswith("Error from getpwuid_r:"),
        ]
    ):
        return None

    match = MACOS_LOG_PREFIX_REGEX.match(line)
    if match:
        groups = match.groupdict()
        return groups["content"], bool(groups["subsystem"])

    return line, False


class XcodeBuildFilter:
    # The prefix for all xcodebuild messages.
    XCODEBUILD_PREFIX = (
        r"\d{4}-\d{2}-\d{2} +\d+:\d{2}:\d{2}\.\d{3} xcodebuild\[\d+:\d+\] +"
    )

    # Xcode 14 generates the following warning on x86_64 hardware
    # 2023-10-04 08:05:21.757 xcodebuild[46899:11335453] DVTCoreDeviceEnabledState:
    #   DVTCoreDeviceEnabledState_Disabled set via user default
    #   (DVTEnableCoreDevice=disabled)
    DEVICE_ENABLED_STATE_RE = re.compile(
        XCODEBUILD_PREFIX
        + r"DVTCoreDeviceEnabledState: DVTCoreDeviceEnabledState_Disabled "
        r"set via user default \(DVTEnableCoreDevice=disabled\)"
    )

    # Xcode 14 generates the following warning when there is a passcode protected device
    # attached to your computer, even if you're not doing anything to target that device:
    # ---------------------------------------------------------------------
    # 2023-09-27 08:38:11.865 xcodebuild[41087:25901835]  DTDKRemoteDeviceConnection:
    #   Failed to start remote service "com.apple.mobile.notification_proxy" on device.
    #   Error: Error Domain=com.apple.dtdevicekit Code=811 "Failed to start remote
    #   service "com.apple.mobile.notification_proxy" on device."
    #   UserInfo={NSUnderlyingError=0x10b8ec780 {Error Domain=
    #   com.apple.dt.MobileDeviceErrorDomain Code=-402653158 "The device is passcode
    #   protected." UserInfo={MobileDeviceErrorCode=(0xE800001A),
    #   com.apple.dtdevicekit.stacktrace=(
    #         0   DTDeviceKitBase ...
    #         ...
    #         21  libsystem_pthread.dylib ...
    # ), DVTRadarComponentKey=261622, NSLocalizedDescription=The device is
    #   passcode protected.}}, NSLocalizedRecoverySuggestion=Please check your
    #   connection to your device., DVTRadarComponentKey=261622,
    #   NSLocalizedDescription=Failed to start remote service
    #   "com.apple.mobile.notification_proxy" on device.}
    # 2023-09-27 08:38:11.903 xcodebuild[41087:25901835] Failed to start service
    #   (com.apple.amfi.lockdown): 0xe800001a
    # ---------------------------------------------------------------------
    # These warnings can be ignored.
    LOCKED_DEVICE_START_RE = re.compile(
        XCODEBUILD_PREFIX
        + r"DTDKRemoteDeviceConnection: Failed to start remote service "
        r"\"com\.apple\.mobile\.notification_proxy\" on device. Error: "
        r"Error Domain=com\.apple\.dtdevicekit Code=811 \"Failed to start "
        r"remote service \"com.apple.mobile.notification_proxy\" on device.\""
    )
    LOCKED_DEVICE_END_RE = re.compile(
        r"\), DVTRadarComponentKey=\d+, NSLocalizedDescription=The device is "
        # r"passcode protected\.}}, NSLocalizedRecoverySuggestion=Please check "
        # r"your connection to your device\."
    )
    LOCKED_DEVICE_ADDITIONAL_RE = re.compile(
        XCODEBUILD_PREFIX + r"Failed to start service \(com\.apple\.amfi\.lockdown\): "
    )

    # XCode 15 generates dozens of copies of the following message:
    # ---------------------------------------------------------------------
    # 2023-09-26 14:35:45.775 xcodebuild[75877:23947967] [MT] DVTAssertions:
    #   Warning in /System/Volumes/Data/SWE/Apps/DT/BuildRoots/BuildRoot11
    #   /ActiveBuildRoot/Library/Caches/com.apple.xbs/Sources/IDEFrameworks
    #   /IDEFrameworks-22267/IDEFoundation/Provisioning/Capabilities Infrastructure
    #   /IDECapabilityQuerySelection.swift:103
    # Details:  createItemModels creation requirements should not create capability
    #   item model for a capability item model that already exists.
    # Function: createItemModels(for:itemModelSource:)
    # Thread:   <_NSMainThread: 0x11d60beb0>{number = 1, name = main}
    # Please file a bug at https://feedbackassistant.apple.com with this warning
    #   message and any useful information you can provide.
    # ---------------------------------------------------------------------
    # As best as I can make out, this is a bug in Xcode; but it's overwhelming and
    # confusing, so filter it out.
    DVT_ASSERTIONS_RE = re.compile(
        XCODEBUILD_PREFIX + r"\[MT\] DVTAssertions: "
        r"Warning in /System/Volumes/Data/SWE/Apps/DT/BuildRoots/BuildRoot11/"
        r"ActiveBuildRoot/Library/Caches/com.apple.xbs/Sources/IDEFrameworks/"
        r"IDEFrameworks-\d+/IDEFoundation/Provisioning"
        r"/Capabilities Infrastructure/IDECapabilityQuerySelection.swift:\d+"
    )

    def __init__(self):
        self.dvt_ignore_count = 0
        self.locked_device = False

    def __call__(self, line):
        """Filter a single line of a log.

        :param line: A single line of raw system log content, including the newline.
        """
        if self.dvt_ignore_count:
            self.dvt_ignore_count -= 1
        elif self.locked_device:
            if self.LOCKED_DEVICE_END_RE.match(line):
                self.locked_device = False
        elif self.LOCKED_DEVICE_START_RE.match(line):
            # Start ignoring content until the end line is found.
            self.locked_device = True
        elif self.LOCKED_DEVICE_ADDITIONAL_RE.match(line):
            # Ignore the additional 1-line warning about failing to start the service.
            pass
        elif self.DEVICE_ENABLED_STATE_RE.match(line):
            # Ignore the DVTCoreDeviceEnabledState warning
            pass
        elif self.DVT_ASSERTIONS_RE.match(line):
            # Ignore the 4 lines after the DVTAssertions message
            self.dvt_ignore_count = 4
        else:
            yield line
