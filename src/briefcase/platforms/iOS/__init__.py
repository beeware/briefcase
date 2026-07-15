from __future__ import annotations

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
        Xcode.verify(self.tools, min_version=(13, 0, 0))

        # Verify superclass tools *after* xcode. This ensures we get the
        # git check *after* the xcode check.
        super().verify_tools()
