import json
import os
import re
import shlex
import shutil
import subprocess
import time
from contextlib import suppress
from pathlib import Path

from briefcase.config import PEP508_NAME_RE
from briefcase.console import InputDisabled, select_option
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidDeviceError,
    MissingToolError,
)
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.java import JDK

DEVICE_NOT_FOUND = re.compile(r"^error: device '[^']*' not found")


class AndroidDeviceNotAuthorized(BriefcaseCommandError):
    def __init__(self, device):
        self.device = device
        super().__init__(
            f"""
The device you have selected ({device}) has not had developer options and
USB debugging enabled. These must be enabled before a device can be used  as a
target for deployment. For details on how to enable Developer Options, visit:

    https://developer.android.com/studio/debug/dev-options#enable

Once you have enabled these options on your device, you will be able to select
this device as a deployment target.

"""
        )


class AndroidSDK(Tool):
    name = "android_sdk"
    full_name = "Android SDK"

    def __init__(self, tools: ToolCache, root_path: Path):
        self.tools = tools
        self.dot_android_path = self.tools.home_path / ".android"
        self.root_path = root_path

        # A wrapper for testing purposes
        self.sleep = time.sleep

    @property
    def cmdline_tools_url(self):
        """The Android SDK Command-Line Tools URL appropriate to the current operating
        system."""
        platform_name = self.tools.host_os.lower()
        if self.tools.host_os.lower() == "darwin":
            platform_name = "mac"
        elif self.tools.host_os.lower() == "windows":
            platform_name = "win"

        return f"https://dl.google.com/android/repository/commandlinetools-{platform_name}-{self.cmdline_tools_version}_latest.zip"  # noqa: E501

    @property
    def cmdline_tools_path(self):
        return self.root_path / "cmdline-tools" / "latest"

    @property
    def cmdline_tools_version(self):
        # This is the version of the Android SDK Command-line tools that
        # are current as of May 2022. These tools can generally self-update,
        # so using a fixed download URL isn't a problem.
        # However, if/when this version number is changed, ensure that the
        # checks done during verification include any required upgrade steps.
        return "8092744"

    @property
    def cmdline_tools_version_path(self):
        return self.root_path / "cmdline-tools" / self.cmdline_tools_version

    @property
    def sdkmanager_path(self):
        sdkmanager = (
            "sdkmanager.bat" if self.tools.host_os == "Windows" else "sdkmanager"
        )
        return self.cmdline_tools_path / "bin" / sdkmanager

    @property
    def adb_path(self):
        adb = "adb.exe" if self.tools.host_os == "Windows" else "adb"
        return self.root_path / "platform-tools" / adb

    @property
    def avdmanager_path(self):
        avdmanager = (
            "avdmanager.bat" if self.tools.host_os == "Windows" else "avdmanager"
        )
        return self.cmdline_tools_path / "bin" / avdmanager

    @property
    def emulator_path(self):
        emulator = "emulator.exe" if self.tools.host_os == "Windows" else "emulator"
        return self.root_path / "emulator" / emulator

    @property
    def avd_path(self):
        return self.dot_android_path / "avd"

    def avd_config_filename(self, avd):
        return self.avd_path / f"{avd}.avd" / "config.ini"

    @property
    def env(self):
        return {
            "ANDROID_SDK_ROOT": os.fsdecode(self.root_path),
            "JAVA_HOME": str(self.tools.java.java_home),
        }

    @property
    def emulator_abi(self):
        """The ABI to use for the Android emulator."""
        if self.tools.host_arch == "arm64" and self.tools.host_os == "Darwin":
            return "arm64-v8a"
        if self.tools.host_arch in ("x86_64", "AMD64"):
            return "x86_64"

        raise BriefcaseCommandError(
            "The Android emulator does not currently support "
            f"{self.tools.host_os} {self.tools.host_arch} hardware."
        )

    @property
    def DEFAULT_DEVICE_TYPE(self):
        return "pixel"

    @property
    def DEFAULT_DEVICE_SKIN(self):
        return "pixel_3a"

    @property
    def DEFAULT_SYSTEM_IMAGE(self):
        return f"system-images;android-31;default;{self.emulator_abi}"

    @classmethod
    def verify(cls, tools: ToolCache, install=True):
        """Verify an Android SDK is available.

        If the ANDROID_SDK_ROOT environment variable is set, that location will
        be checked for a valid SDK.

        If the location provided doesn't contain an SDK, or no location is provided,
        an SDK is downloaded.

        :param tools: ToolCache of available tools
        :param install: Should the tool be installed if it is not found?
        :returns: A valid Android SDK wrapper. If Android SDK is not
            available, and was not installed, raises MissingToolError.
        """
        # short circuit since already verified and available
        if hasattr(tools, "android_sdk"):
            return tools.android_sdk

        JDK.verify(tools=tools, install=install)

        sdk = None
        sdk_root = tools.os.environ.get("ANDROID_SDK_ROOT")
        if sdk_root:
            sdk = AndroidSDK(tools=tools, root_path=Path(sdk_root))

            if sdk.exists():
                sdk.verify_license()
            else:
                sdk = None
                tools.logger.warning(
                    f"""
*************************************************************************
** WARNING: ANDROID_SDK_ROOT does not point to an Android SDK          **
*************************************************************************

    The location pointed to by the ANDROID_SDK_ROOT environment
    variable:

    {sdk_root}

    doesn't appear to contain an Android SDK.

    Briefcase will use its own SDK instance.

*************************************************************************
"""
                )

        if sdk is None:
            # Build an SDK wrapper for the Briefcase SDK instance.
            sdk_root_path = tools.base_path / "android_sdk"
            sdk = AndroidSDK(tools=tools, root_path=sdk_root_path)

            if sdk.exists():
                # NOTE: For now, all known versions of the cmdline-tools are compatible.
                # If/when that ever changes, do a verification check here.
                sdk.verify_license()
            else:
                # The legacy SDK Tools exist. Delete them.
                if (sdk_root_path / "tools").exists():
                    tools.logger.warning(
                        f"""
*************************************************************************
** WARNING: Upgrading Android SDK tools                                **
*************************************************************************

    Briefcase needs to replace the older Android SDK Tools with the
    newer Android SDK Command-Line Tools. This will involve some large
    downloads, as well as re-accepting the licenses for the Android
    SDKs.

    Any emulators created with the older Android SDK Tools will not be
    compatible with the new tools. You will need to create new
    emulators. Old emulators can be removed by deleting the files
    in {sdk.avd_path} matching the emulator name.

*************************************************************************
"""
                    )
                    tools.shutil.rmtree(sdk_root_path)

                if install:
                    tools.logger.info(
                        "The Android SDK was not found; downloading and installing...",
                        prefix=cls.name,
                    )
                    sdk.install()
                else:
                    raise MissingToolError("Android SDK")

        tools.android_sdk = sdk
        return sdk

    def exists(self):
        """Confirm that the SDK actually exists.

        Look for the sdkmanager; and, if necessary, confirm that it is executable.
        """
        return self.sdkmanager_path.is_file() and (
            self.tools.host_os == "Windows"
            or self.tools.os.access(self.sdkmanager_path, self.tools.os.X_OK)
        )

    @property
    def managed_install(self):
        """Is the Android SDK install managed by Briefcase?"""
        # Although the end-user can provide their own SDK, the SDK also
        # provides a built-in upgrade mechanism. Therefore, all Android SDKs
        # are managed installs.
        return True

    def install(self):
        """Download and install the Android SDK."""
        cmdline_tools_zip_path = self.tools.download.file(
            url=self.cmdline_tools_url,
            download_path=self.tools.base_path,
            role="Android SDK Command-Line Tools",
        )

        # The cmdline-tools package *must* be installed as:
        #     <sdk_path>/cmdline-tools/latest
        #
        # However, the zip file unpacks a top-level folder named `cmdline-tools`.
        # So, the unpacking process is:
        #
        #  1. Make a <sdk_path>/cmdline-tools folder
        #  2. Unpack the zip file into that folder, creating <sdk_path>/cmdline-tools/cmdline-tools
        #  3. Move <sdk_path>/cmdline-tools/cmdline-tools to <sdk_path>/cmdline-tools/latest
        #  4. Drop a marker file named <sdk_path>/cmdline-tools/<version> so we can track
        #     the version that was installed.

        with self.tools.input.wait_bar("Installing Android SDK Command-Line Tools..."):
            self.cmdline_tools_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self.tools.shutil.unpack_archive(
                    cmdline_tools_zip_path, extract_dir=self.cmdline_tools_path.parent
                )
            except (shutil.ReadError, EOFError) as e:
                raise BriefcaseCommandError(
                    f"""\
Unable to unpack Android SDK Command-Line Tools ZIP file. The download may have been interrupted
or corrupted.

Delete {cmdline_tools_zip_path} and run briefcase again.
"""
                ) from e

            # If there's an existing version of the cmdline tools (or the version marker), delete them.
            if self.cmdline_tools_path.exists():
                self.tools.shutil.rmtree(self.cmdline_tools_path)
            if self.cmdline_tools_version_path.exists():
                self.tools.os.unlink(self.cmdline_tools_version_path)

            # Rename the top level zip content to the final name
            (self.cmdline_tools_path.parent / "cmdline-tools").rename(
                self.cmdline_tools_path
            )
            # Touch a file with the version that was installed.
            self.cmdline_tools_version_path.touch()

            # Zip file no longer needed once unpacked.
            cmdline_tools_zip_path.unlink()

            # Python zip unpacking ignores permission metadata.
            # On non-Windows, we manually fix permissions.
            if self.tools.host_os != "Windows":
                for binpath in (self.cmdline_tools_path / "bin").glob("*"):
                    if not self.tools.os.access(binpath, self.tools.os.X_OK):
                        binpath.chmod(0o755)

        # Licences must be accepted.
        self.verify_license()

    def upgrade(self):
        """Upgrade the Android SDK."""
        try:
            # Using subprocess.run() with no I/O redirection so the user sees
            # the full output and can send input.
            self.tools.subprocess.run(
                [os.fsdecode(self.sdkmanager_path), "--update"],
                env=self.env,
                check=True,
                stream_output=False,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"""\
Error while updating the Android SDK manager. Please run this command and examine
its output for errors.

    $ {self.sdkmanager_path} --update
"""
            ) from e

    def list_packages(self):
        """In debug output, list the packages currently managed by the SDK."""
        try:
            # check_output always writes its output to debug
            self.tools.subprocess.check_output(
                [os.fsdecode(self.sdkmanager_path), "--list_installed"],
                env=self.env,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Unable to invoke the Android SDK manager"
            ) from e

    def adb(self, device):
        """Obtain an ADB instance for managing a specific device.

        :param device: The device ID to manage.
        """
        return ADB(self.tools, device=device)

    def verify_license(self):
        """Verify that all necessary licenses have been accepted.

        If they haven't, prompt the user to do so.

        Raises an error if licenses are not.
        """
        license_path = self.root_path / "licenses" / "android-sdk-license"
        if license_path.exists():
            return

        self.tools.logger.info(
            """
The Android tools provided by Google have license terms that you must accept
before you may use those tools.
"""
        )
        try:
            # Using subprocess.run() with no I/O redirection so the user sees
            # the full output and can send input.
            self.tools.subprocess.run(
                [os.fsdecode(self.sdkmanager_path), "--licenses"],
                env=self.env,
                check=True,
                stream_output=False,
            )
        except (subprocess.CalledProcessError, OSError) as e:
            raise BriefcaseCommandError(
                f"""\
Error while reviewing Android SDK licenses. Please run this command and examine
its output for errors.

    $ {self.sdkmanager_path} --licenses
"""
            ) from e

        if not license_path.exists():
            raise BriefcaseCommandError(
                """\
You did not accept the Android SDK licenses. Please re-run the briefcase command
and accept the Android SDK license when prompted. You may need an Internet
connection.
"""
            )

    def verify_emulator(self):
        """Verify that Android emulator has been installed, and is in a runnable state.

        Raises an error if the emulator can't be installed.
        """
        # Ensure the `platforms` folder exists.
        # See the discussion on #766 for details; as of June 2022, if this folder
        # doesn't exist, the emulator won't start, raising the error:
        #
        #    PANIC: Cannot find AVD system path. Please define ANDROID_SDK_ROOT
        #
        # Creating an empty platforms folder is enough to overcome this. This folder
        # will be created automatically when you build a project; but if you have a
        # clean Android SDK install that hasn't been used to build a project, it
        # might be missing.
        (self.root_path / "platforms").mkdir(exist_ok=True)

        if self.emulator_path.exists():
            self.tools.logger.debug("Android emulator is already installed.")
            return

        self.tools.logger.info("Downloading the Android emulator...")
        try:
            self.tools.subprocess.run(
                [
                    os.fsdecode(self.sdkmanager_path),
                    "platform-tools",
                    "emulator",
                ],
                env=self.env,
                check=True,
                stream_output=False,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "Error while installing Android emulator."
            ) from e

    def verify_avd(self, avd):
        """Verify that the AVD has the necessary system components to launch.

        This includes:
            * AVD system image
            * Emulator skin

        :param avd: The AVD name to verify.
        """
        # Read the AVD configuration to retrieve the system image.
        # This is stored in the AVD configuration file with the key:
        #   image.sysdir.1=system-images/android-31/default/arm64-v8a/
        avd_config = self.avd_config(avd)

        try:
            system_image_path = Path(avd_config["image.sysdir.1"])

            # Convert the path into a system image name, and verify it.
            self.verify_system_image(";".join(system_image_path.parts))
        except KeyError:
            self.tools.logger.warning(
                f"""
*************************************************************************
** WARNING: Unable to determine AVD system image                       **
*************************************************************************

    Briefcase was unable to determine the system image of the Android
    emulator AVD {avd!r} from it's configuration file.

    Briefcase will proceed assuming the emulator is correctly
    configured. If you experience any problems running the emulator,
    this may be the cause of the problem.

*************************************************************************
"""
            )

        try:
            skin = avd_config["skin.name"]
            skin_path = Path(avd_config["skin.path"])
            if skin_path == Path("_no_skin"):
                self.tools.logger.debug("Emulator does not use a skin.")
            elif skin_path != Path("skins") / skin:
                self.tools.logger.warning(
                    f"""
*************************************************************************
** WARNING: Unrecognized device skin                                   **
*************************************************************************

    Briefcase does not recognize the skin {skin!r} used by the
    Android emulator AVD {avd!r}.

    Briefcase will proceed assuming the emulator is correctly
    configured. If you experience any problems running the emulator,
    this may be the cause of the problem.

*************************************************************************
"""
                )
            else:
                # Convert the path into a system image name, and verify it.
                self.verify_emulator_skin(skin)

        except KeyError:
            self.tools.logger.debug(f"Device {avd!r} doesn't define a skin.")

    def verify_system_image(self, system_image):
        """Verify that the required system image is installed.

        :param system_image: The SDKManager identifier for the system
            image (e.g., ``"system-images;android-31;default;x86_64"``)
        """
        # Look for the directory named as a system image.
        # If it exists, we already have the system image.
        system_image_parts = system_image.split(";")

        if len(system_image_parts) < 4 or system_image_parts[0] != "system-images":
            raise BriefcaseCommandError(
                f"{system_image!r} is not a valid system image name."
            )

        if system_image_parts[-1] != self.emulator_abi:
            self.tools.logger.warning(
                f"""
*************************************************************************
** WARNING: Unexpected emulator ABI                                    **
*************************************************************************

    The system image {system_image!r}
    does not match the architecture of this computer ({self.emulator_abi}).

    Briefcase will proceed assuming the emulator is correctly
    configured. If you experience any problems running the emulator,
    this may be the cause of the problem.

*************************************************************************
"""
            )

        # Convert the system image into a path where that system image
        # would be expected, and see if the location exists.
        system_image_path = self.root_path
        for part in system_image_parts:
            system_image_path = system_image_path / part

        if system_image_path.exists():
            # Found the system image.
            return

        # System image not found; download it.
        self.tools.logger.info(
            f"Downloading the {system_image!r} Android system image...",
            prefix=self.name,
        )
        try:
            self.tools.subprocess.run(
                [
                    os.fsdecode(self.sdkmanager_path),
                    system_image,
                ],
                env=self.env,
                check=True,
                stream_output=False,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Error while installing the {system_image!r} Android system image."
            ) from e

    def verify_emulator_skin(self, skin):
        """Verify that an emulator skin is available.

        A human-readable list of available skins can be found here:

            https://android.googlesource.com/platform/tools/adt/idea/+/refs/heads/mirror-goog-studio-main/artwork/resources/device-art-resources/

        :param skin: The name of the skin to obtain
        """
        # Check for a device skin. If it doesn't exist, download it.
        skin_path = self.root_path / "skins" / skin
        if skin_path.exists():
            self.tools.logger.debug(f"Device skin {skin!r} already exists.")
            return

        self.tools.logger.info(f"Obtaining {skin} device skin...", prefix=self.name)

        skin_url = (
            "https://android.googlesource.com/platform/tools/adt/idea/"
            "+archive/refs/heads/mirror-goog-studio-main/"
            f"artwork/resources/device-art-resources/{skin}.tar.gz"
        )

        skin_tgz_path = self.tools.download.file(
            url=skin_url,
            download_path=self.root_path,
            role=f"{skin} device skin",
        )

        # Unpack skin archive
        with self.tools.input.wait_bar("Installing device skin..."):
            try:
                self.tools.shutil.unpack_archive(skin_tgz_path, extract_dir=skin_path)
            except (shutil.ReadError, EOFError) as err:
                raise BriefcaseCommandError(
                    f"Unable to unpack {skin} device skin."
                ) from err

            # Delete the downloaded file.
            skin_tgz_path.unlink()

    def emulators(self):
        """Find the list of emulators that are available."""
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            output = self.tools.subprocess.check_output(
                [os.fsdecode(self.emulator_path), "-list-avds"]
            ).strip()

            # AVD names are returned one per line.
            if len(output) == 0:
                return []
            return output.split("\n")
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Unable to obtain Android emulator list") from e

    def devices(self):
        """Find the devices that are attached and available to ADB."""
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            output = self.tools.subprocess.check_output(
                [os.fsdecode(self.adb_path), "devices", "-l"]
            ).strip()

            # Process the output of `adb devices -l`.
            # The first line is header information.
            # Each subsequent line is a single device descriptor.
            devices = {}
            header_found = False
            for line in output.split("\n"):
                if line == "List of devices attached":
                    header_found = True
                elif header_found and line:
                    parts = re.sub(r"\s+", " ", line).split(" ")

                    details = {}
                    for part in parts[2:]:
                        key, value = part.split(":")
                        details[key] = value

                    if parts[1] == "device":
                        try:
                            name = details["model"].replace("_", " ")
                        except KeyError:
                            name = "Unknown device (no model name)"
                        authorized = True
                    elif parts[1] == "offline":
                        name = "Unknown device (offline)"
                        authorized = False
                    else:
                        name = "Unknown device (not authorized for development)"
                        authorized = False

                    devices[parts[0]] = {
                        "name": name,
                        "authorized": authorized,
                    }

            return devices
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Unable to obtain Android device list") from e

    def select_target_device(self, device_or_avd):
        """Select a device to be the target for actions.

        Interrogates the system to get the list of available devices.

        If the user has specified a device at the command line, that device will
        be validated, and then automatically selected.

        :param device_or_avd: The device or AVD to target. Can be a physical
            device id (a hex string), an emulator id (``emulator-5554``), or an
            emulator AVD name (``@robotfriend``), or a JSON payload describing
            the properties of an emulator that will be created (e.g.,
            ``'{"avd":"beePhone","device_type":"pixel","skin":"pixel_3a","system_image":"system-images;android-31;default;arm64-v8a"}'``)
            If ``None``, the user will be asked to select a device from the list
            available.
        :returns: A tuple containing ``(device, name, avd)``. ``avd`` will only
            be provided if an emulator with that AVD is not currently running.
            If ``device`` is null, a new emulator should be created.
        """
        # If the device_or_avd starts with "{", it's a definition for a new
        # emulator to be created.
        if device_or_avd and device_or_avd.startswith("{"):
            try:
                emulator_config = json.loads(device_or_avd)
                emulators = set(self.emulators())

                # If an emulator with this AVD already exists, use it
                avd = emulator_config["avd"]
                if avd not in emulators:
                    self._create_emulator(**emulator_config)

                return None, f"@{avd} (emulator)", avd
            except json.JSONDecodeError as e:
                raise BriefcaseCommandError(
                    f"Unable to create emulator with definition {device_or_avd!r}"
                ) from e
            except KeyError:
                raise BriefcaseCommandError("No AVD provided for new device.")
            except TypeError as e:
                property = str(e).split(" ")[-1]
                raise BriefcaseCommandError(f"Unknown device property {property}.")

        # Get the list of attached devices (includes running emulators)
        running_devices = self.devices()

        # Choices is an ordered list of options that can be shown to the user.
        # Each device should appear only once, and be keyed by AVD only if
        # a device ID isn't available.
        choices = []
        # Device choices is the full lookup list. Devices can be looked up
        # by any valid key - ID *or* AVD.
        device_choices = {}

        # Iterate over all the running devices.
        # If the device is a virtual device, use ADB to get the emulator AVD name.
        # If it is a physical device, use the device name.
        # Keep a log of all running AVDs
        running_avds = {}
        for d, details in sorted(running_devices.items(), key=lambda d: d[1]["name"]):
            name = details["name"]
            avd = self.adb(d).avd_name()
            if avd:
                # It's a running emulator
                running_avds[avd] = d
                full_name = f"@{avd} (running emulator)"
                choices.append((d, full_name))

                # Save the AVD as a device detail.
                details["avd"] = avd

                # Device can be looked up by device ID or AVD
                device_choices[d] = full_name
                device_choices[f"@{avd}"] = full_name
            else:
                # It's a physical device (might be disabled)
                full_name = f"{name} ({d})"
                choices.append((d, full_name))
                device_choices[d] = full_name

        # Add any non-running emulator AVDs to the list of candidate devices
        for avd in self.emulators():
            if avd not in running_avds:
                name = f"@{avd} (emulator)"
                choices.append((f"@{avd}", name))
                device_choices[f"@{avd}"] = name

        # If a device or AVD has been provided, check it against the available
        # device list.
        if device_or_avd:
            try:
                name = device_choices[device_or_avd]

                if device_or_avd.startswith("@"):
                    # specifier is an AVD
                    try:
                        avd = device_or_avd[1:]
                        device = running_avds[avd]
                    except KeyError:
                        # device_or_avd isn't in the list of running avds;
                        # it must be a non-running emulator.
                        return None, name, avd
                else:
                    # Specifier is a direct device ID
                    avd = None
                    device = device_or_avd

                details = running_devices[device]
                avd = details.get("avd")
                if details["authorized"]:
                    # An authorized, running device (emulator or physical)
                    return device, name, avd
                else:
                    # An unauthorized physical device
                    raise AndroidDeviceNotAuthorized(device)

            except KeyError as e:
                # Provided device_or_id isn't a valid device identifier.
                id_type = (
                    "emulator AVD" if device_or_avd.startswith("@") else "device ID"
                )
                raise InvalidDeviceError(id_type, device_or_avd) from e
        # We weren't given a device/AVD; we have to select from the list.
        # If we're selecting from a list, there's always one last choice
        choices.append((None, "Create a new Android emulator"))

        # Show the choices to the user.
        self.tools.input.prompt()
        self.tools.input.prompt("Select device:")
        self.tools.input.prompt()
        try:
            choice = select_option(choices, input=self.tools.input)
        except InputDisabled as e:
            # If input is disabled, and there's only one actual simulator,
            # select it. If there are no simulators, select "Create simulator"
            if len(choices) <= 2:
                choice = choices[0][0]
            else:
                raise BriefcaseCommandError(
                    """\
Input has been disabled; can't select a device to target.
Use the -d/--device option to explicitly specify the device to use.
"""
                ) from e

        # Process the user's choice
        if choice is None:
            # Create a new emulator. No device ID or AVD.
            device = None
            avd = None
            name = None
        elif choice.startswith("@"):
            # A non-running emulator. We have an AVD, but no device ID.
            device = None
            name = device_choices[choice]
            avd = choice[1:]
        else:
            # Either a running emulator, or a physical device. Regardless,
            # we need to check if the device is developer enabled.
            # Functionally, we know the the device *must* be in the list of
            # choices; which means it's also in the list of running devices
            # and the list of device choices, so any KeyError on those lookups
            # indicates a deeper problem.
            details = running_devices[choice]
            if not details["authorized"]:
                # An unauthorized physical device
                raise AndroidDeviceNotAuthorized(choice)

            # Return the device ID and name.
            device = choice
            name = device_choices[choice]
            avd = details.get("avd")

        if avd:
            self.tools.logger.info(
                f"""
In future, you can specify this device by running:

    $ briefcase run android -d "@{avd}"
"""
            )
        elif device:
            self.tools.logger.info(
                f"""
In future, you can specify this device by running:

    $ briefcase run android -d {device}
"""
            )

        return device, name, avd

    def create_emulator(self, use_defaults=False):
        """Create a new Android emulator.

        :param use_defaults: Should the emulator be created with defaults?
        :returns: The AVD of the newly created emulator.
        """
        # Get the list of existing emulators
        emulators = set(self.emulators())

        default_avd = "beePhone"
        i = 1
        # Make sure the default name is unique
        while default_avd in emulators:
            i += 1
            default_avd = f"beePhone{i}"

        # Prompt for a device avd until a valid one is provided.
        self.tools.logger.info(
            f"""
You need to select a name for your new emulator. This is an identifier that
can be used to start the emulator in future. It should follow the same naming
conventions as a Python package (i.e., it may only contain letters, numbers,
hyphens and underscores). If you don't provide a name, Briefcase will use the
a default name '{default_avd}'.

"""
        )
        avd_is_invalid = True
        while avd_is_invalid:
            avd = self.tools.input(f"Emulator name [{default_avd}]: ")
            # If the user doesn't provide a name, use the default.
            if avd == "":
                avd = default_avd

            if not PEP508_NAME_RE.match(avd):
                self.tools.logger.info(
                    f"""
'{avd}' is not a valid emulator name. An emulator name may only contain
letters, numbers, hyphens and underscores.

"""
                )
            elif avd in emulators:
                self.tools.logger.info(
                    f"""
An emulator named '{avd}' already exists.

"""
                )
                self.tools.logger.info()
            else:
                avd_is_invalid = False

        # TODO: Provide a list of options for device types with matching skins
        device_type = self.DEFAULT_DEVICE_TYPE
        skin = self.DEFAULT_DEVICE_SKIN

        # TODO: Provide a list of options for system images.
        system_image = self.DEFAULT_SYSTEM_IMAGE

        self._create_emulator(
            avd=avd,
            device_type=device_type,
            skin=skin,
            system_image=system_image,
        )

        self.tools.logger.info(
            f"""
Android emulator '{avd}' created.

In future, you can specify this device by running:

    $ briefcase run android -d @{avd}
"""
        )

        return avd

    def _create_emulator(
        self,
        avd,
        device_type=None,
        skin=None,
        system_image=None,
    ):
        """Internal method that does the actual work of creating the emulator.

        AVD is the only required argument; all other arguments will assume
        reasonable defaults.

        :param avd: The AVD for the new emulator
        :param device_type: The device type for the new emulator (e.g., "pixel")
        :param skin: The skin for the new emulator to use (e.g., "pixel_3a")
        :param system_image: The system image to use on the new emulator.
            (e.g., "system-images;android-31;default;arm64-v8a")
        """
        if device_type is None:
            device_type = self.DEFAULT_DEVICE_TYPE
        if skin is None:
            skin = self.DEFAULT_DEVICE_SKIN
        if system_image is None:
            system_image = self.DEFAULT_SYSTEM_IMAGE

        # Ensure the required skin is available.
        self.verify_emulator_skin(skin)

        # Ensure the required system image is available.
        self.verify_system_image(system_image)

        with self.tools.input.wait_bar(f"Creating Android emulator {avd}..."):
            try:
                self.tools.subprocess.check_output(
                    [
                        os.fsdecode(self.avdmanager_path),
                        "--verbose",
                        "create",
                        "avd",
                        "--name",
                        avd,
                        "--abi",
                        self.emulator_abi,
                        "--package",
                        system_image,
                        "--device",
                        device_type,
                    ],
                    env=self.env,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Unable to create Android emulator") from e

        with self.tools.input.wait_bar("Adding extra device configuration..."):
            self.update_emulator_config(
                avd,
                {
                    "avd.id": avd,
                    "avd.name": avd,
                    "disk.dataPartition.size": "4096M",
                    "hw.keyboard": "yes",
                    "skin.dynamic": "yes",
                    "skin.name": skin,
                    "skin.path": f"skins/{skin}",
                    "showDeviceFrame": "yes",
                },
            )

    def avd_config(self, avd):
        """Obtain the AVD configuration as key-value pairs.

        :params avd: The AVD whose config will be retrieved
        """
        # Parse the existing config into key-value pairs
        avd_config = {}
        try:
            with self.avd_config_filename(avd).open("r") as f:
                for line in f:
                    try:
                        key, value = line.rstrip().split("=", 1)
                        avd_config[key.strip()] = value.strip()
                    except ValueError:
                        pass
        except OSError as e:
            raise BriefcaseCommandError(
                f"Unable to read configuration of AVD @{avd}"
            ) from e

        return avd_config

    def update_emulator_config(self, avd, updates):
        """Update the AVD configuration with specific values.

        :params avd: The AVD whose config will be updated
        :params updates: A dictionary containing the new key-value to
            add to the device configuration.
        """
        avd_config = self.avd_config(avd)

        # Augment the config with the new key-values pairs
        avd_config.update(updates)

        # Write the update configuration.
        with self.avd_config_filename(avd).open("w") as f:
            for key, value in avd_config.items():
                f.write(f"{key}={value}\n")

    def start_emulator(self, avd, extra_args=None):
        """Start an existing Android emulator.

        Returns when the emulator is booted and ready to accept apps.

        :param avd: The AVD of the device.
        :param extra_args: Additional command line arguments to pass when
            starting the emulator.
        """
        if avd not in set(self.emulators()):
            raise InvalidDeviceError("emulator AVD", avd)

        if extra_args is None:
            extra_args = []

        emulator_popen = self.tools.subprocess.Popen(
            [
                os.fsdecode(self.emulator_path),
                f"@{avd}",
                "-dns-server",
                "8.8.8.8",
            ]
            + extra_args,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            start_new_session=True,
        )

        # wrap AVD name in quotes since '@' is a special char in PowerShell
        emulator_command = " ".join(
            f'"{arg}"' if arg.startswith("@") else arg
            for arg in map(str, emulator_popen.args)
        )

        error_msg = (
            "{prologue}"
            + f"""

Try starting the emulator manually by running:

    $ {emulator_command}

Resolve any problems you discover, then try running your app again. You may
find this page helpful in diagnosing emulator problems.

    https://developer.android.com/studio/run/emulator-acceleration#accel-vm
"""
        )

        # The boot process happens in 2 phases.
        # First, the emulator appears in the device list. However, it's
        # not ready until the boot process has finished. To determine
        # the boot status, we need the device ID, and an ADB connection.

        # Phase 1: Wait for the device to appear so we can get an
        # ADB instance for the new device.
        try:
            with self.tools.input.wait_bar("Starting emulator..."):
                adb = None
                known_devices = set()
                while adb is None:
                    if emulator_popen.poll() is not None:
                        raise BriefcaseCommandError(
                            error_msg.format(
                                prologue="Android emulator was unable to start!"
                            )
                        )

                    for device, details in sorted(self.devices().items()):
                        # Only process authorized devices that we haven't seen.
                        if details["authorized"] and device not in known_devices:
                            adb = self.adb(device)
                            device_avd = adb.avd_name()

                            if device_avd == avd:
                                # Found an active device that matches
                                # the AVD we are starting.
                                full_name = f"@{avd} (running emulator)"
                                break
                            else:
                                # Not the one. Zathras knows.
                                adb = None
                                known_devices.add(device)

                    # If we haven't found a device, try again in 2 seconds...
                    if adb is None:
                        self.sleep(2)

            # Phase 2: Wait for the boot process to complete
            if not adb.has_booted():
                with self.tools.input.wait_bar("Booting emulator..."):
                    while not adb.has_booted():
                        if emulator_popen.poll() is not None:
                            raise BriefcaseCommandError(
                                error_msg.format(
                                    prologue="Android emulator was unable to boot!"
                                )
                            )

                        # Try again in 2 seconds...
                        self.sleep(2)
        except BaseException as e:
            # if the emulator exited, this should return its output immediately;
            # if it is still running, this will quickly time out and print nothing.
            with suppress(subprocess.TimeoutExpired):
                self.tools.logger.info(emulator_popen.communicate(timeout=1)[0])

            # Provide troubleshooting steps if user gives up on the emulator starting
            if isinstance(e, KeyboardInterrupt):
                self.tools.logger.warning()
                self.tools.logger.warning(
                    error_msg.format(
                        prologue="Is the Android emulator not starting up properly?"
                    )
                )

            raise

        # Return the device ID and full name.
        return device, full_name


class ADB:
    def __init__(self, tools: ToolCache, device: str):
        """An API integration for the Android Debug Bridge (ADB).

        :param tools: ToolCache of available tools
        :param device: The ID of the device to target (in a format usable by
            `adb -s`)
        """
        self.tools = tools
        self.device = device

    def avd_name(self):
        """Get the AVD name for the device.

        :returns: The AVD name for the device; or ``None`` if the device isn't
            an emulator
        """
        try:
            output = self.run("emu", "avd", "name")
            return output.split("\n")[0]
        except subprocess.CalledProcessError as e:
            # Status code 1 is a normal "it's not an emulator" error response
            if e.returncode == 1:
                return None
            else:
                raise BriefcaseCommandError(
                    f"Unable to interrogate AVD name of device {self.device}"
                ) from e

    def has_booted(self):
        """Determine if the device has completed booting.

        :returns True if it has booted; False otherwise.
        """
        try:
            # When the sys.boot_completed property of the device
            # returns '1', the boot is complete. Any other response indicates
            # booting is underway.
            output = self.run("shell", "getprop", "sys.boot_completed")
            return output.strip() == "1"
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to determine if emulator {self.device} has booted."
            ) from e

    def run(self, *arguments, quiet=False):
        """Run a command on a device using Android debug bridge, `adb`. The device name
        is mandatory to ensure clarity in the case of multiple attached devices.

        :param arguments: List of strings to pass to `adb` as arguments.
        :param quiet: Should the invocation of this command be silent, and
            *not* appear in the logs? This should almost always be False;
            however, for some calls (most notably, calls that are called
            frequently to evaluate the status of another process), logging can
            be turned off so that log output isn't corrupted by thousands of
            polling calls.
        :returns: `adb` output on success; raises an exception on failure.
        """
        # The ADB integration operates on the basis of running commands before
        # checking that they are valid, then parsing output to notice errors.
        # This keeps performance good in the success case.
        try:
            # Capture `stderr` so that if the process exits with failure, the
            # stderr data is in `e.output`.
            return self.tools.subprocess.check_output(
                [
                    os.fsdecode(self.tools.android_sdk.adb_path),
                    "-s",
                    self.device,
                ]
                + [
                    (os.fsdecode(arg) if isinstance(arg, Path) else arg)
                    for arg in arguments
                ],
                quiet=quiet,
            )
        except subprocess.CalledProcessError as e:
            if any(DEVICE_NOT_FOUND.match(line) for line in e.output.split("\n")):
                raise InvalidDeviceError("device id", self.device) from e
            raise

    def install_apk(self, apk_path):
        """Install an APK file on an Android device.

        :param apk_path: The path of the Android APK file to install.

        Returns `None` on success; raises an exception on failure.
        """
        try:
            self.run("install", "-r", apk_path)
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to install APK {apk_path} on {self.device}"
            ) from e

    def force_stop_app(self, package):
        """Force-stop an app, specified as a package name.

        :param package: The name of the Android package, e.g., com.username.myapp.

        Returns `None` on success; raises an exception on failure.
        """
        # In my testing, `force-stop` exits with status code 0 (success) so long
        # as you pass a package name, even if the package does not exist, or the
        # package is not running.
        try:
            self.run("shell", "am", "force-stop", package)
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to force stop app {package} on {self.device}"
            ) from e

    def start_app(self, package, activity, passthrough):
        """Start an app, specified as a package name & activity name.

        :param package: The name of the Android package, e.g., com.username.myapp.
        :param activity: The activity of the APK to start.
        :param passthrough: Arguments to pass to the app.

        Returns `None` on success; raises an exception on failure.

        If you have an APK file, and you are not sure of the package or activity
        name, you can find it using `aapt dump badging filename.apk` and looking
        for "package" and "launchable-activity" in the output.
        """
        try:
            # `am start` also accepts string array extras, but we pass the arguments as a
            # single JSON string, because JSON deals with edge cases like whitespace and
            # escaping in a reliable and well-documented way.
            output = self.run(
                "shell",
                "am",
                "start",
                "-n",
                f"{package}/{activity}",
                "-a",
                "android.intent.action.MAIN",
                "-c",
                "android.intent.category.LAUNCHER",
                "--es",
                "org.beeware.ARGV",
                shlex.quote(json.dumps(passthrough)),  # Protect from Android's shell
            )

            # `adb shell am start` always exits with status zero. We look for error
            # messages in the output.
            if any(
                line.startswith("Error: Activity class ")
                and line.endswith("does not exist.")
                for line in output.split("\n")
            ):
                raise BriefcaseCommandError(
                    f"""\
Activity class not found while starting app.

`adb` output:

    {output}
"""
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to start {package}/{activity} on {self.device}"
            ) from e

    def logcat(self, pid):
        """Start following the adb log for the device.

        :param pid: The PID whose logs you want to display.
        :returns: A Popen object for the logcat call
        """
        return self.tools.subprocess.Popen(
            [
                os.fsdecode(self.tools.android_sdk.adb_path),
                "-s",
                self.device,
                "logcat",
                "--pid",  # This option is available since API level 24.
                pid,
            ]
            # Filter out some noisy and useless tags.
            + [f"{tag}:S" for tag in ["EGL_emulation"]],
            env=self.tools.android_sdk.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

    def logcat_tail(self, since=None):
        """Show the tail of the logs for Python-like apps, starting from a given
        timestamp.

        :param since: The start time from which logs should be displayed
        """
        try:
            self.tools.subprocess.run(
                [
                    os.fsdecode(self.tools.android_sdk.adb_path),
                    "-s",
                    self.device,
                    "logcat",
                    "-t",
                    since.strftime("%m-%d %H:%M:%S.000000"),
                    "-s",
                    # This is a collection of log labels that should catch
                    # most Python app output.
                    "MainActivity:*",
                    "stdio:*",
                    "python.stdout:*",
                    "AndroidRuntime:*",
                ],
                env=self.tools.android_sdk.env,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Error starting ADB logcat.") from e

    def pidof(self, package, **kwargs):
        """Obtain the PID of a running app by package name.

        :param package: The package ID for the application (e.g.,
            ``org.beeware.tutorial``)
        :returns: The PID of the given app as a string, or None if it isn't
        running.
        """
        # The pidof command is available since API level 24. The level 23 emulator image also
        # includes it, but it doesn't work correctly (it returns all processes).
        try:
            # Exit status is unreliable: some devices (e.g. Nexus 4) return 0 even when no
            # process was found.
            return self.run("shell", "pidof", "-s", package, **kwargs).strip() or None
        except subprocess.CalledProcessError:
            return None

    def pid_exists(self, pid, **kwargs):
        """Confirm if the PID exists on the emulator.

        :param pid: The PID to check
        :returns: True if the PID exists, False if it doesn't.
        """
        # Look for the existence of /proc/<PID> on the device filesystem.
        # If that file exists, so does the process.
        try:
            self.run("shell", "test", "-e", f"/proc/{pid}", **kwargs)
            return True
        except subprocess.CalledProcessError:
            return False

    def kill(self):
        """Stop the running Android emulator."""
        try:
            self.run("emu", "kill")
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Error starting ADB logcat.") from e
