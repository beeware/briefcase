from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Generator

# winreg can only be imported on Windows
try:
    import winreg
except ImportError:
    winreg = None

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache


class WindowsSDK(Tool):
    name = "windows_sdk"
    full_name = "Windows SDK"
    SDK_VERSION = "10.0"
    # Oldest supported SDK version is 10.0.15063.0
    SDK_MIN_VERSION = 15063
    # Registry path to keys with details of the installed Windows SDKs
    SDK_KEY = rf"SOFTWARE\Microsoft\Microsoft SDKs\Windows\v{SDK_VERSION}"
    # Subkey containing the installation directory for the SDK
    SDK_DIR_KEY = "InstallationFolder"
    # Subkey for "latest" installed SDK version
    SDK_VERSION_KEY = "ProductVersion"
    # As a fallback, possible default locations for SDK
    DEFAULT_SDK_DIRS = [
        Path(rf"C:\Program Files (x86)\Windows Kits\{SDK_VERSION.split('.')[0]}")
    ]
    # Installing parts of the SDK for UWP apps is not inherently required; however,
    # it is the minimum selection that ensures the signing tool has the libraries
    # necessary to run. Executables from older versions of the SDK may not be
    # compatible with the version of Windows that's installed.
    SDK_REQUIRED_COMPONENTS = """
    * Windows SDK Signing Tools for Desktop Apps
    * Windows SDK for UWP Managed Apps
"""

    def __init__(self, tools: ToolCache, root_path: Path, version: str, arch: str):
        """Create a wrapper around the Windows SDK.

        :param tools: ToolCache of available tools
        :param root_path: Base path for sdk, e.g. C:/Program Files (x86)/Windows Kits/10/
        :param version: Full SDK version, e.g. 10.0.22621.0
        :param arch: Host architecture for SDK, e.g. x64, arm64, etc
        """
        self.tools = tools
        self.root_path = root_path
        self.version = version
        self.arch = arch

    @property
    def bin_path(self) -> Path:
        return self.root_path / "bin" / self.version / self.arch

    @property
    def signtool_exe(self) -> Path:
        return self.bin_path / "signtool.exe"

    @classmethod
    def _sdk_versions_from_bin(cls, sdk_dir: Path) -> list[str]:
        """Returns list of SDK versions from the install location bin directory."""
        bin_dir = sdk_dir / "bin"
        # prioritize newer versions of the SDK
        version_dirs = sorted(bin_dir.glob(f"{cls.SDK_VERSION}.*.0/"), reverse=True)
        return [d.name for d in version_dirs]

    @classmethod
    def _windows_sdks(cls, tools: ToolCache) -> Generator[tuple[Path, str], None, None]:
        """Generator of (path, version) for instances of Windows SDK.

        All instances of Windows SDK should reside in the same base directory;
        this is enforced by the SDK installer. Certain subdirectories, such as
        `include` and `bin`, will contain subdirectories for versions that may
        be installed.
        """
        tools.logger.debug("Finding Suitable Installation...", prefix=cls.full_name)

        # Return user-specified SDK
        if (environ_sdk_dir := tools.os.environ.get("WindowsSDKDir")) and (
            environ_sdk_version := tools.os.environ.get("WindowsSDKVersion")
        ):
            yield Path(environ_sdk_dir), environ_sdk_version
            raise BriefcaseCommandError(
                f"""\
The 'WindowsSDKDir' and 'WindowsSDKVersion' environment variables do not point
to a valid install of the Windows SDK v{cls.SDK_VERSION}:

WindowsSDKDir:     {environ_sdk_dir}
WindowsSDKVersion: {environ_sdk_version}
"""
            )

        # To support the varied bitness of processes and installations within Windows,
        # the registry is split among different views to avoid a process naively and
        # likely unintentionally referencing incompatible software/settings. This is
        # accomplished with subkeys under the primary trees, for example:
        #   HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node
        # A 32-bit version of the registry tree is effectively mirrored under this
        # subkey for a 64-bit Windows installation.
        access_right_precedence = [
            # 32-bit process sees 32-bit registry; 64-bit process sees 64-bit registry
            winreg.KEY_READ,
            # 32-bit process sees 32-bit registry; 64-bit process sees 32-bit registry
            winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
            # 32-bit process sees 64-bit registry; 64-bit process sees 64-bit registry
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ]

        registry_tree_order = (
            (hkey, access)
            for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
            for access in access_right_precedence
        )

        for hkey, access in registry_tree_order:
            try:
                with winreg.OpenKeyEx(hkey, cls.SDK_KEY, access=access) as key:
                    if not (sdk_dir := winreg.QueryValueEx(key, cls.SDK_DIR_KEY)[0]):
                        continue
                    if not (sdk_dir := Path(tools.os.fsdecode(sdk_dir))).is_dir():
                        continue

                    # Return the "latest" installed SDK first
                    if reg_version := winreg.QueryValueEx(key, cls.SDK_VERSION_KEY)[0]:
                        # Append missing "servicing" revision to registry version
                        reg_version = f"{reg_version}.0"
                        tools.logger.debug(
                            f"Evaluating Registry SDK version '{reg_version}' at {sdk_dir}"
                        )
                        yield sdk_dir, reg_version

                    # Return other versions of the SDK installed in sdk_dir
                    for sdk_version in cls._sdk_versions_from_bin(sdk_dir):
                        if sdk_version != reg_version:
                            tools.logger.debug(
                                f"Evaluating Registry SDK Bin version '{sdk_version}' at {sdk_dir}"
                            )
                            yield sdk_dir, sdk_version
            except FileNotFoundError:
                pass  # ignore missing registry keys

        for sdk_dir in cls.DEFAULT_SDK_DIRS:
            if sdk_dir.is_dir():
                for sdk_version in cls._sdk_versions_from_bin(sdk_dir):
                    tools.logger.debug(
                        f"Evaluating Default Bin SDK version '{sdk_version}' at {sdk_dir}"
                    )
                    yield sdk_dir, sdk_version

    @classmethod
    def _is_supported_version(cls, sdk: WindowsSDK) -> bool:
        """Returns whether the version of the SDK install is supported."""
        try:
            version_split = sdk.version.split(".")
            if not sdk.version.startswith(cls.SDK_VERSION):
                return False
            if int(version_split[2]) < cls.SDK_MIN_VERSION:
                return False
        except (AttributeError, ValueError, IndexError):
            return False

        return True

    @classmethod
    def _verify_signtool(cls, sdk: WindowsSDK) -> bool:
        """Returns SDK if signtool exists and can successfully run."""
        if not sdk.signtool_exe.is_file():
            return False

        try:
            sdk.tools.subprocess.check_output([sdk.signtool_exe, "-?"])
        except (OSError, subprocess.CalledProcessError):
            # Windows can raise OSError when it cannot run signtool. This can happen
            # when an old version of the SDK is installed and only signtool is installed.
            return False

        return True

    @classmethod
    def verify(cls, tools: ToolCache):
        """Verify the Windows SDK is installed with needed components.

        :param tools: ToolCache of available tools
        """
        # short circuit since already verified and available
        if hasattr(tools, "windows_sdk"):
            return tools.windows_sdk

        arch = {"AMD64": "x64", "ARM64": "arm64"}.get(tools.host_arch, tools.host_arch)

        sdk = None
        for sdk_dir, sdk_version in cls._windows_sdks(tools):
            sdk = WindowsSDK(tools, root_path=sdk_dir, version=sdk_version, arch=arch)

            if not cls._is_supported_version(sdk):
                sdk = None
                continue

            if not cls._verify_signtool(sdk):
                sdk = None
                continue

            break

        if sdk is None:
            raise BriefcaseCommandError(
                f"""\
Unable to locate a suitable Windows SDK v{cls.SDK_VERSION} installation.

Ensure at least v{cls.SDK_VERSION}.{cls.SDK_MIN_VERSION}.0 is installed and the components below are included:
{cls.SDK_REQUIRED_COMPONENTS}
See https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/ to install the SDK.
"""
            )

        tools.logger.debug(f"Using Windows SDK v{sdk.version} at {sdk.root_path}")
        tools.windows_sdk = sdk
        return sdk

    @property
    def managed_install(self):
        return False
