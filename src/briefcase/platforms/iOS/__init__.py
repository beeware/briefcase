from __future__ import annotations

import datetime
from collections.abc import Collection
from typing import TYPE_CHECKING

from briefcase.integrations.xcode import Xcode

if TYPE_CHECKING:
    from briefcase.commands.base import BaseCommand

    _MixinBase = BaseCommand
else:
    _MixinBase = object

DEFAULT_OUTPUT_FORMAT = "Xcode"


class iOSMixin(_MixinBase):
    platform = "iOS"
    supported_host_os: Collection[str] = {"Darwin"}
    supported_host_os_reason = (
        "iOS applications require Xcode, which is only available on macOS."
    )
    # 0.3.20 introduced PEP 730-style dynamic libraries.
    platform_target_version: str | None = "0.3.20"

    def verify_tools(self):
        # In April each year, the iOS App Store requires that apps submitted to
        # the iOS App Store are built with the SDK that was released the
        # previous year (but has the *current* year number). For example,
        # iOS/Xcode 26 was released in September 2025; in April 2026, all apps
        # had to be built against the iOS 26 SDK.
        now = datetime.datetime.now(tz=datetime.UTC)
        major = now.year % 100
        if now.month < 4:
            major = major - 1
        Xcode.verify(self.tools, min_version=f"{major}.0")

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()
