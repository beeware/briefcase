from unittest.mock import MagicMock

import pytest

from briefcase.commands import UpgradeCommand
from briefcase.console import Console, Log
from briefcase.exceptions import MissingToolError


class DummyUpgradeCommand(UpgradeCommand):
    """A dummy upgrade command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    platform = "tester"
    output_format = "dummy"
    description = "Dummy update command"

    def __init__(self, *args, sdks, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, **kwargs)

        self.sdks = sdks

    def bundle_path(self, app):
        return self.platform_path / f"{app.app_name}.dummy"

    def binary_path(self, app):
        return self.platform_path / f"{app.app_name}.dummy.bin"

    def distribution_path(self, app, packaging_format):
        return self.platform_path / f"{app.app_name}.dummy.{packaging_format}"


@pytest.fixture
def ManagedSDK1():
    sdk = MagicMock()
    sdk.verify.return_value = sdk
    sdk.name = "managed-1"
    sdk.full_name = "Managed 1"
    sdk.exists.return_value = True
    sdk.managed_install = True
    # No plugins defined on SDK1
    sdk.plugins.values.side_effect = AttributeError
    return sdk


@pytest.fixture
def ManagedSDK2Plugin1():
    sdk = MagicMock()
    sdk.verify.return_value = sdk
    sdk.name = "managed-2-plugin-1"
    sdk.full_name = "Managed 2 plugin 1"
    sdk.exists.return_value = True
    sdk.managed_install = True
    return sdk


@pytest.fixture
def ManagedSDK2Plugin2():
    sdk = MagicMock()
    sdk.verify.return_value = sdk
    sdk.name = "managed-2-plugin-2"
    sdk.full_name = "Managed 2 plugin 2"
    sdk.exists.return_value = True
    sdk.managed_install = True
    return sdk


@pytest.fixture
def ManagedSDK2Plugin3():
    sdk = MagicMock()
    sdk.verify.return_value = sdk
    sdk.name = "managed-2-plugin-3"
    sdk.full_name = "Managed 2 plugin 3"
    sdk.exists.return_value = False
    sdk.verify.side_effect = MissingToolError("managed-2-plugin-3")
    sdk.managed_install = True
    return sdk


@pytest.fixture
def ManagedSDK2(ManagedSDK2Plugin1, ManagedSDK2Plugin2, ManagedSDK2Plugin3):
    sdk = MagicMock()
    sdk.verify.return_value = sdk
    sdk.name = "managed-2"
    sdk.full_name = "Managed 2"
    sdk.exists.return_value = True
    sdk.managed_install = True
    sdk.plugins = {
        "managed2-plugin1": ManagedSDK2Plugin1,
        "managed2-plugin2": ManagedSDK2Plugin2,
        "managed2-plugin3": ManagedSDK2Plugin3,
    }
    return sdk


@pytest.fixture
def NonManagedSDK():
    sdk = MagicMock()
    sdk.verify.return_value = sdk
    sdk.name = "non-managed"
    sdk.full_name = "Non Managed"
    sdk.exists.return_value = True
    sdk.managed_install = False
    return sdk


@pytest.fixture
def NonInstalledSDK():
    sdk = MagicMock()
    sdk.name = "non-installed"
    sdk.full_name = "Non Installed"
    sdk.verify.side_effect = MissingToolError("non-installed")
    return sdk


@pytest.fixture
def upgrade_command(tmp_path, ManagedSDK1, ManagedSDK2, NonManagedSDK, NonInstalledSDK):
    return DummyUpgradeCommand(
        base_path=tmp_path,
        sdks=[
            ManagedSDK1,
            NonManagedSDK,
            NonInstalledSDK,
            ManagedSDK2,
        ],
    )
