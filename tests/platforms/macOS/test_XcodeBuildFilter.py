# This file contains raw log lines, which are extremely long. Turn of the flake8 rule
# for line length.
# flake8: noqa: E501
import pytest

from briefcase.platforms.macOS.filters import XcodeBuildFilter


@pytest.mark.parametrize(
    "original, filtered",
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
                '2023-09-27 08:38:11.865 xcodebuild[41087:25901835]  DTDKRemoteDeviceConnection: Failed to start remote service "com.apple.mobile.notification_proxy" on device. Error: Error Domain=com.apple.dtdevicekit Code=811 "Failed to start remote service "com.apple.mobile.notification_proxy" on device." UserInfo={NSUnderlyingError=0x10b8ec780 {Error Domain=com.apple.dt.MobileDeviceErrorDomain Code=-402653158 "The device is passcode protected." UserInfo={MobileDeviceErrorCode=(0xE800001A), com.apple.dtdevicekit.stacktrace=(',
                "        0   DTDeviceKitBase                     0x00000001288ff298 DTDKCreateNSErrorFromAMDErrorCode + 300",
                "        1   DTDeviceKitBase                     0x000000012890ba38 __63-[DTDKRemoteDeviceConnection startFirstServiceOf:unlockKeybag:]_block_invoke + 380",
                "        2   DTDeviceKitBase                     0x000000012890b248 __48-[DTDKRemoteDeviceConnection futureWithSession:]_block_invoke_4 + 28",
                "        3   DTDeviceKitBase                     0x0000000128901460 __DTDKExecuteInSession_block_invoke_2 + 68",
                "        4   DTDeviceKitBase                     0x0000000128900af0 __DTDKExecuteWithConnection_block_invoke_2 + 216",
                "        5   DTDeviceKitBase                     0x00000001289009e8 __DTDKExecuteWithConnection_block_invoke + 112",
                "        6   libdispatch.dylib                   0x00000001a81b4400 _dispatch_client_callout + 20",
                "        7   libdispatch.dylib                   0x00000001a81c397c _dispatch_lane_barrier_sync_invoke_and_complete + 56",
                "        8   DVTFoundation                       0x0000000100fa8014 DVTDispatchBarrierSync + 148",
                "        9   DVTFoundation                       0x0000000100f842b4 -[DVTDispatchLock performLockedBlock:] + 60",
                "        10  DTDeviceKitBase                     0x00000001289008e4 DTDKExecuteWithConnection + 200",
                "        11  DTDeviceKitBase                     0x00000001289012e4 DTDKExecuteInSession + 260",
                "        12  DTDeviceKitBase                     0x000000012890b028 __48-[DTDKRemoteDeviceConnection futureWithSession:]_block_invoke_2 + 204",
                "        13  DVTFoundation                       0x0000000100fa7330 __DVT_CALLING_CLIENT_BLOCK__ + 16",
                "        14  DVTFoundation                       0x0000000100fa7d58 __DVTDispatchAsync_block_invoke + 152",
                "        15  libdispatch.dylib                   0x00000001a81b2874 _dispatch_call_block_and_release + 32",
                "        16  libdispatch.dylib                   0x00000001a81b4400 _dispatch_client_callout + 20",
                "        17  libdispatch.dylib                   0x00000001a81bba88 _dispatch_lane_serial_drain + 668",
                "        18  libdispatch.dylib                   0x00000001a81bc62c _dispatch_lane_invoke + 436",
                "        19  libdispatch.dylib                   0x00000001a81c7244 _dispatch_workloop_worker_thread + 648",
                "        20  libsystem_pthread.dylib             0x00000001a8360074 _pthread_wqthread + 288",
                "        21  libsystem_pthread.dylib             0x00000001a835ed94 start_wqthread + 8",
                '), DVTRadarComponentKey=261622, NSLocalizedDescription=The device is passcode protected.}}, NSLocalizedRecoverySuggestion=Please check your connection to your "device., DVTRadarComponentKey=261622, NSLocalizedDescription=Failed to start remote service "com.apple.mobile.notification_proxy" on device.}',
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
                "2023-09-27 09:09:55.400 xcodebuild[44887:25948169] Failed to start service (com.apple.amfi.lockdown): 0xe800001a",
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
                "2023-10-04 08:05:21.757 xcodebuild[46899:11335453] DVTCoreDeviceEnabledState: DVTCoreDeviceEnabledState_Disabled set via user default (DVTEnableCoreDevice=disabled)",
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
                "2023-09-26 14:35:45.775 xcodebuild[75877:23947967] [MT] DVTAssertions: Warning in /System/Volumes/Data/SWE/Apps/DT/BuildRoots/BuildRoot11/ActiveBuildRoot/Library/Caches/com.apple.xbs/Sources/IDEFrameworks/IDEFrameworks-22267/IDEFoundation/Provisioning/Capabilities Infrastructure/IDECapabilityQuerySelection.swift:103",
                "Details: createItemModels creation requirements should not create capability item model for a capability item model that already exists.",
                "Function: createItemModels(for:itemModelSource:)",
                "Thread:   <_NSMainThread: 0x11d60beb0>{number = 1, name = main}",
                "Please file a bug at https://feedbackassistant.apple.com with this warning message and any useful information you can provide.",
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
