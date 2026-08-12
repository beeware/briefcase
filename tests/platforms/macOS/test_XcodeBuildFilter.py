import pytest

from briefcase.platforms.macOS.filters import XcodeBuildFilter


@pytest.mark.parametrize(
    ("original", "filtered"),
    [
        # Nothing to filter
        (
            [
                "'Twas brillig, and the slithy toves",
                "Did gyre and gimble in the wabe;",
                "All mimsy were the borogoves,",
                "And the mome raths outgrabe.",
            ],
            [
                "'Twas brillig, and the slithy toves",
                "Did gyre and gimble in the wabe;",
                "All mimsy were the borogoves,",
                "And the mome raths outgrabe.",
            ],
        ),
        # Xcode 14: DTDKRemoteDeviceConnection warning about locked attached devices
        (
            [
                "'Twas brillig, and the slithy toves",
                (
                    "2023-09-27 08:38:11.865 xcodebuild[41087:25901835]  "
                    "DTDKRemoteDeviceConnection: Failed to start remote service "
                    '"com.apple.mobile.notification_proxy" on device. Error: Error '
                    'Domain=com.apple.dtdevicekit Code=811 "Failed to start remote '
                    'service "com.apple.mobile.notification_proxy" on device." '
                    "UserInfo={NSUnderlyingError=0x10b8ec780 {Error "
                    "Domain=com.apple.dt.MobileDeviceErrorDomain Code=-402653158 "
                    '"The device is passcode protected." '
                    "UserInfo={MobileDeviceErrorCode=(0xE800001A), "
                    "com.apple.dtdevicekit.stacktrace=("
                ),
                (
                    "        0   DTDeviceKitBase                     "
                    "0x00000001288ff298 DTDKCreateNSErrorFromAMDErrorCode + 300"
                ),
                (
                    "        1   DTDeviceKitBase                     "
                    "0x000000012890ba38 __63-[DTDKRemoteDeviceConnection "
                    "startFirstServiceOf:unlockKeybag:]_block_invoke + 380"
                ),
                (
                    "), DVTRadarComponentKey=261622, NSLocalizedDescription=The "
                    "device is passcode protected.}}, NSLocalizedRecoverySuggestion="
                    'Please check your connection to your "device., '
                    "DVTRadarComponentKey=261622, NSLocalizedDescription=Failed to "
                    'start remote service "com.apple.mobile.notification_proxy" '
                    "on device.}"
                ),
                "Did gyre and gimble in the wabe;",
            ],
            [
                "'Twas brillig, and the slithy toves",
                "Did gyre and gimble in the wabe;",
            ],
        ),
        # Xcode 14: Additional locking-related message.
        (
            [
                "'Twas brillig, and the slithy toves",
                (
                    "2023-09-27 09:09:55.400 xcodebuild[44887:25948169] Failed to "
                    "start service (com.apple.amfi.lockdown): 0xe800001a"
                ),
                "Did gyre and gimble in the wabe;",
            ],
            [
                "'Twas brillig, and the slithy toves",
                "Did gyre and gimble in the wabe;",
            ],
        ),
        # XCode 14: x86_64 "device enabled state" warning.
        (
            [
                "'Twas brillig, and the slithy toves",
                (
                    "2023-10-04 08:05:21.757 xcodebuild[46899:11335453] "
                    "DVTCoreDeviceEnabledState: DVTCoreDeviceEnabledState_Disabled "
                    "set via user default (DVTEnableCoreDevice=disabled)"
                ),
                "Did gyre and gimble in the wabe;",
            ],
            [
                "'Twas brillig, and the slithy toves",
                "Did gyre and gimble in the wabe;",
            ],
        ),
        # Xcode 15: DVTAssertions warning about createItemModels
        (
            [
                "'Twas brillig, and the slithy toves",
                (
                    "2023-09-26 14:35:45.775 xcodebuild[75877:23947967] [MT] "
                    "DVTAssertions: Warning in /System/Volumes/Data/SWE/Apps/DT/"
                    "BuildRoots/BuildRoot11/ActiveBuildRoot/Library/Caches/"
                    "com.apple.xbs/Sources/IDEFrameworks/IDEFrameworks-22267/"
                    "IDEFoundation/Provisioning/Capabilities Infrastructure/"
                    "IDECapabilityQuerySelection.swift:103"
                ),
                (
                    "Details: createItemModels creation requirements should not "
                    "create capability item model for a capability item model that "
                    "already exists."
                ),
                "Function: createItemModels(for:itemModelSource:)",
                "Thread:   <_NSMainThread: 0x11d60beb0>{number = 1, name = main}",
                (
                    "Please file a bug at https://feedbackassistant.apple.com with "
                    "this warning message and any useful information you can provide."
                ),
                "Did gyre and gimble in the wabe;",
            ],
            [
                "'Twas brillig, and the slithy toves",
                "Did gyre and gimble in the wabe;",
            ],
        ),
    ],
)
def test_filter(original, filtered):
    """The Xcode build output filters out ignorable warnings."""
    xcode_filter = XcodeBuildFilter()

    output = []
    for raw_line in original:
        for line in xcode_filter(raw_line):
            output.append(line)

    assert output == filtered
