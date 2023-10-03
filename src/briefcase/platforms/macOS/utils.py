import concurrent
import email
import hashlib
import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError


def sha256_file_digest(path: Path) -> bytes:
    """Compute a sha256 checksum digest of a file.

    :param path: The file to digest.
    :returns: A sha256 digest for the file.
    """
    with path.open("rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.digest()


class AppPackageMergeMixin:
    def lipo_dylib(self, relative_path: Path, target_path: Path, sources: list[Path]):
        """Create a fat library by invoking lipo on multiple source libraries.

        :param relative_path: The path fragment for the dylib, relative to the root
        :param target_path: The root location where the fat library will be written
        :param sources: A list of root locations providing single platform libraries.
        """
        self.logger.info(f"Creating fat library {relative_path}")
        try:
            self.tools.subprocess.run(
                [
                    "lipo",
                    "-create",
                    "-output",
                    target_path / relative_path,
                ]
                # Add all the constructed source paths. If the original binary is
                # universal, or the binary is only needed on *some* platforms (e.g.,
                # libjpeg isn't included in the x86_64 Pillow wheel), the source won't
                # exist, so only merge sources that actually exist. lipo allows
                # creating a "fat" single-platform binary; it's effectively a copy.
                + [
                    source_path / relative_path
                    for source_path in sources
                    if (source_path / relative_path).is_file()
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to create fat library for {relative_path}"
            ) from e

    def merge_app_packages(
        self,
        target_app_packages: Path,
        sources: list[Path],
    ):
        """Merge the contents of multiple source app packages into a final location.

        :param target_app_packages: The location of the final merged app packages
        :param sources: A list of app packages folders to be merged.
        """
        # Clear any existing app packages folder.
        if target_app_packages.is_dir():
            self.tools.shutil.rmtree(target_app_packages)
        self.tools.os.mkdir(target_app_packages)

        dylibs = []
        digests = {}
        for source_app_packages in sources:
            with self.input.wait_bar(f"Merging {source_app_packages.name}..."):
                for source_path in source_app_packages.glob("**/*"):
                    relative_path = source_path.relative_to(source_app_packages)
                    target_path = target_app_packages / relative_path
                    if source_path.is_dir():
                        target_path.mkdir(exist_ok=True)
                    else:
                        if source_path.suffix in {".so", ".dylib"}:
                            # Dynamic libraries need to be merged; do this in a second pass.
                            dylibs.append(relative_path)
                        elif target_path.exists():
                            # The file already exists. Check for differences; if there are any
                            # differences outside `dist-info` or `__pycache__` folders, warn
                            # the user.
                            digest = sha256_file_digest(source_path)
                            if digests[relative_path] != digest and not (
                                relative_path.parent.name == "__pycache__"
                                or Path(relative_path.parts[0]).suffix == ".dist-info"
                            ):
                                self.logger.warning(
                                    f"{relative_path} has different content "
                                    f"between sources; ignoring {source_app_packages.suffix[1:]} version."
                                )
                        else:
                            # The file doesn't exist yet; copy it as is, and store the
                            # digest for later comparison
                            self.tools.shutil.copyfile(source_path, target_path)
                            digests[relative_path] = sha256_file_digest(source_path)

        # Call lipo on each dylib to create the fat version.
        progress_bar = self.input.progress_bar()
        task_id = progress_bar.add_task("Creating fat libraries...", total=len(dylibs))
        with progress_bar:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for relative_path in dylibs:
                    future = executor.submit(
                        self.lipo_dylib,
                        target_path=target_app_packages,
                        relative_path=relative_path,
                        sources=sources,
                    )
                    futures.append(future)
                for future in concurrent.futures.as_completed(futures):
                    progress_bar.update(task_id, advance=1)
                    if future.exception():
                        raise future.exception()


def find_binary_packages(
    install_path: Path, universal_suffix: str = None
) -> list[tuple[str, str]]:
    """Find the packages that have been installed that have binary components.

    :param install_path: The path into which packages have been installed.
    :param universal_suffix: The tag suffix that indicates a universal wheel.
    """
    binary_packages = []
    for distinfo in install_path.glob("**/*.dist-info"):
        # Read the WHEEL file in the dist-info folder.
        # Use this to determine if the wheel is "pure", and the tag
        # for the wheel.
        with (distinfo / "WHEEL").open("r", encoding="utf-8") as f:
            wheel_data = email.message_from_string(f.read())
            is_purelib = wheel_data["Root-Is-Purelib"] == "true"
            tag = wheel_data["Tag"]

        # If the wheel is pure, it's not a binary package
        if is_purelib:
            continue

        # If the tag ends with the universal tag, the binary package can be used on all
        # targets, and doesn't need additional processing.
        if universal_suffix and tag.endswith(universal_suffix):
            continue

        # The wheel is a single platform binary wheel.
        # Read the package metadata to determine what needs to be installed.
        with (distinfo / "METADATA").open("r", encoding="utf-8") as f:
            metadata = email.message_from_string(f.read())
            binary_packages.append((metadata["Name"], metadata["Version"]))

    return binary_packages
