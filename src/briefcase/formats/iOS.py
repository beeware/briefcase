from __future__ import annotations

from pathlib import Path

from briefcase.config import AppConfig
from briefcase.exceptions import NoDistributionArtefact
from briefcase.formats.base import BasePackagingFormat


class iOSIPAPackagingFormat(BasePackagingFormat):
    @property
    def name(self) -> str:
        return "ipa"

    def distribution_path(self, app: AppConfig) -> Path:
        # This path won't ever be *generated*, as distribution artefacts
        # can't be generated on iOS.
        raise NoDistributionArtefact("""
*************************************************************************
** WARNING: No distributable artefact has been generated               **
*************************************************************************

    Briefcase has not generated a standalone iOS artefact, as iOS apps
    must be published through Xcode.

    To open Xcode for your iOS project, run:

        briefcase open iOS

    and use Xcode's app distribution workflow described at:

        https://briefcase.readthedocs.io/en/stable/reference/platforms/iOS/xcode.html#ios-deploy

*************************************************************************
""")

    def package_app(self, app: AppConfig, **kwargs):
        # The distribution_path call will raise the warning if anyone calls it.
        # But for iOS, we don't actually build anything in 'package'.
        self.distribution_path(app)

    def priority(self, app: AppConfig) -> int:
        return 10
