from pathlib import Path
from typing import Generator, List, Tuple

from briefcase.exceptions import BriefcaseCommandError, MissingToolError
from briefcase.integrations.base import Tool, ToolCache

# winreg can only be imported on Windows
try:
    import winreg
except ImportError:
    winreg = None


class WindowsSDK(Tool):
    name = "windows_sdk"
    full_name = "Windows SDK"
    sdk_version = "10.0"

    def __init__(self, tools: ToolCache, root_path: Path, version: str, arch: str):
        """Create a wrapper around the Windows SDK.

        :param tools: ToolCache of available tools
        :param root_path: Base path for sdk, e.g. C:/Program Files (x86)/Windows Kits/10/
        :param version: Full SDK version, e.g. 10.0.14393.0
        :param arch: Host architecture for SDK, e.g. x64, arm64, etc
        """
        self.tools = tools
        self.root_path = root_path
        self.version = version
        self.arch = arch

    @property
    def bin_path(self):
        return self.root_path / "bin" / self.version / self.arch

    @property
    def signtool_exe(self):
        return self.bin_path / "signtool.exe"

    @classmethod
    def _sdk_versions_from_bin(cls, sdk_dir: Path) -> List[str]:
        """Returns list of SDK versions from the install location bin directory."""
        bin_dir = sdk_dir / "bin"
        # prioritize newer versions of the SDK
        version_dirs = sorted(bin_dir.glob(f"{cls.sdk_version}.*.0/"), reverse=True)
        return [d.name for d in version_dirs]

    @classmethod
    def _windows_sdks(cls, tools: ToolCache) -> Generator[Tuple[Path, str], None, None]:
        """Generator of (path, version) for instances of Windows SDK.

        All instances of Windows SDK should reside in the same base directory;
        this is enforced by the SDK installer. Certain subdirectories, such as
        `include` and `bin`, will contain subdirectories for versions that may
        be installed.
        """
        tools.logger.debug("Finding Suitable Installation...", prefix=cls.full_name)
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
        # Path to keys with details of the installed Windows SDKs
        sdk_key = rf"SOFTWARE\Microsoft\Microsoft SDKs\Windows\v{cls.sdk_version}"
        # Subkey containing the installation directory for the SDK
        install_dir_subkey = "InstallationFolder"
        # Subkey for "latest" installed SDK version
        version_subkey = "ProductVersion"
        # As a fallback, possible default locations for SDK
        default_directories = [Path(r"C:\Program Files (x86)\Windows Kits\10")]

        # Return user-specified SDK first
        if environ_sdk_dir := tools.os.environ.get("WindowsSDKDir"):
            if environ_sdk_version := tools.os.environ.get("WindowsSDKVersion"):
                yield environ_sdk_dir, environ_sdk_version
                raise BriefcaseCommandError(
                    f"""\
The 'WindowsSDKDir' and 'WindowsSDKVersion' environment variables do not point
to a valid install of the Windows SDK v{cls.sdk_version}:

    WindowsSDKDir:     {environ_sdk_dir}
    WindowsSDKVersion: {environ_sdk_version}
"""
                )

        seen_sdk_dirs: set[Path] = set()
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
                            tools.logger.debug(
                                f"Evaluating Registry SDK version '{reg_version}' at {sdk_dir}"
                            )
                            # Append missing "servicing" revision to registry version
                            yield sdk_dir, f"{reg_version}.0"

                        # Return SDKs that may be installed at sdk_dir location
                        for sdk_version in cls._sdk_versions_from_bin(sdk_dir):
                            if not sdk_version == reg_version:
                                tools.logger.debug(
                                    f"Evaluating Registry SDK Bin version '{sdk_version}' at {sdk_dir}"
                                )
                                yield sdk_dir, sdk_version

                        seen_sdk_dirs.add(sdk_dir)
                except FileNotFoundError:
                    pass  # ignore missing registry keys

        for sdk_dir in default_directories:
            if sdk_dir not in seen_sdk_dirs and sdk_dir.is_dir():
                for sdk_version in cls._sdk_versions_from_bin(sdk_dir):
                    tools.logger.debug(
                        f"Evaluating Default Bin SDK version '{sdk_version}' at {sdk_dir}"
                    )
                    yield sdk_dir, sdk_version

    @classmethod
    def verify(cls, tools: ToolCache):
        """Verify the Windows SDK is installed with needed components.

        :param tools: ToolCache of available tools
        """
        # short circuit since already verified and available
        if hasattr(tools, "windows_sdk"):
            return tools.windows_sdk

        arch = {"AMD64": "x64", "ARM64": "arm64"}.get(tools.host_arch, tools.host_arch)

        windows_sdk = None
        for sdk_dir, sdk_version in cls._windows_sdks(tools):
            # The code signing tool `signtool.exe` must exist
            if not (sdk_dir / "bin" / sdk_version / arch / "signtool.exe").is_file():
                continue

            windows_sdk = WindowsSDK(
                tools=tools,
                root_path=sdk_dir,
                version=sdk_version,
                arch=arch,
            )
            break

        if windows_sdk is None:
            raise MissingToolError(f"Windows SDK v{cls.sdk_version}")

        tools.logger.debug(f"Using Windows SDK v{sdk_version} at {sdk_dir}")
        tools.windows_sdk = windows_sdk
        return windows_sdk

    @property
    def managed_install(self):
        return False
