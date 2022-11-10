from importlib.util import find_spec
from pathlib import Path
from typing import Generator, Tuple

from briefcase.exceptions import MissingToolError

# winreg can only be imported on Windows
if find_spec("winreg"):
    import winreg


class WindowsSDK:
    name = "windows_sdk"
    full_name = "Windows SDK"

    def __init__(self, tools, root_path: Path, version: str):
        """Create a wrapper around the Windows SDK signtool.exe.

        :param tools: ToolCache of available tools.
        """
        self.tools = tools
        self.root_path = root_path
        self.version = version

    @property
    def bin_path(self):
        return self.root_path / "bin" / self.version / "x64"

    @property
    def signtool_exe(self):
        return self.bin_path / "signtool.exe"

    @classmethod
    def _windows_sdks(cls, tools) -> Generator[Tuple[Path, str], None, None]:
        """Generator of (path, version) for instances of Windows SDK v10.

        All instances of Windows SDK v10 should reside in the same base
        directory. Certain subdirectories, such as `include` and `bin`,
        will contain subdirectories for versions that may be installed.
        """
        access_right_precedence = [
            # 32-bit process sees 32-bit registry; 64-bit process sees 64-bit registry
            winreg.KEY_READ,
            # 32-bit process sees 32-bit registry; 64-bit process sees 32-bit registry
            winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
            # 32-bit process sees 64-bit registry; 64-bit process sees 64-bit registry
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ]
        # Key specifying the filesystem location for v10 of Windows SDK
        sdk_key = r"SOFTWARE\Microsoft\Microsoft SDKs\Windows\v10.0"
        # Sub-key containing the installation directory for the SDK
        install_dir_subkey = "InstallationFolder"
        # Sub-key for latest installed SDK version
        version_subkey = "ProductVersion"
        # As last resort fallback, possible default locations for SDK
        default_directories = [Path(r"C:\Program Files (x86)\Windows Kits\10")]

        # Return user-specified SDK first
        if environ_sdk := tools.os.environ.get("WindowsSdkDir"):
            if environ_sdk_version := tools.os.environ.get("WindowsSDKVersion"):
                yield environ_sdk, environ_sdk_version
                # TODO:PR: consider raising here if user's SDK is rejected

        seen_sdk_dirs = set()
        for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for access_right in access_right_precedence:
                try:
                    with winreg.OpenKeyEx(hkey, sdk_key, access=access_right) as key:

                        sdk_dir, key_type = winreg.QueryValueEx(key, install_dir_subkey)
                        if key_type != winreg.REG_SZ or not sdk_dir:
                            continue

                        sdk_dir = Path(sdk_dir)
                        if sdk_dir in seen_sdk_dirs or not sdk_dir.is_dir():
                            continue

                        # Return the "latest" installed SDK first
                        reg_version, key_type = winreg.QueryValueEx(key, version_subkey)
                        if key_type == winreg.REG_SZ and reg_version:
                            # the registry doesn't have the "servicing" version part
                            reg_version += ".0"
                            yield sdk_dir, reg_version

                        # Return SDKs that may be installed at sdk_dir location
                        inferred_versions = reversed(
                            [d.name for d in (sdk_dir / "bin").glob("10.*.*.0/")]
                        )
                        for version in inferred_versions:
                            if not version == reg_version:
                                yield sdk_dir, version

                        seen_sdk_dirs.add(sdk_dir)
                except FileNotFoundError:
                    pass  # ignore missing keys

        for sdk_dir in default_directories:
            if sdk_dir not in seen_sdk_dirs and sdk_dir.is_dir():
                yield sdk_dir, None

    @classmethod
    def verify(cls, tools):
        """Verify the Windows SDK installed with needed components.

        :param tools: ToolCache of available tools
        """
        # short circuit since already verified and available
        if hasattr(tools, "windows_sdk"):
            return tools.windows_sdk

        windows_sdk = None
        for sdk_dir, sdk_version in cls._windows_sdks(tools):

            # The code signing tool `signtool.exe` must exist
            if not (sdk_dir / "bin" / sdk_version / "x64" / "signtool.exe").is_file():
                continue

            windows_sdk = cls(tools=tools, root_path=sdk_dir, version=sdk_version)
            break

        if windows_sdk is None:
            raise MissingToolError("Windows SDK v10")

        tools.windows_sdk = windows_sdk
        return windows_sdk

    @property
    def managed_install(self):
        return False
