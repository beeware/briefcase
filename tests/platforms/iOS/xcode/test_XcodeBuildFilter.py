import pytest

from briefcase.platforms.iOS.xcode import XcodeBuildFilter


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
        # DVTAssertions warning about createItemModels
        (
            [
                "'Twas brillig, and the slithy toves",
                (
                    "2023-09-26 14:35:45.775 xcodebuild[75877:23947967] [MT] "
                    "DVTAssertions: Warning in /System/Volumes/Data/SWE/Apps"
                    "/DT/BuildRoots/BuildRoot11/ActiveBuildRoot/Library/Caches"
                    "/com.apple.xbs/Sources/IDEFrameworks/IDEFrameworks-22267"
                    "/IDEFoundation/Provisioning/Capabilities Infrastructure"
                    "/IDECapabilityQuerySelection.swift:103"
                ),
                (
                    "Details: createItemModels creation requirements should "
                    "not create capability item model for a capability item "
                    "model that already exists."
                ),
                "Function: createItemModels(for:itemModelSource:)",
                "Thread:   <_NSMainThread: 0x11d60beb0>{number = 1, name = main}",
                (
                    "Please file a bug at https://feedbackassistant.apple.com "
                    "with this warning message and any useful information you "
                    "can provide."
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
