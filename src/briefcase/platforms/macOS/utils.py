from __future__ import annotations

import concurrent
import email
import hashlib
import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError


def sha256_file_digest(path: Path) -> str:
    """Compute a sha256 checksum digest of a file.

    :param path: The file to digest.
    :returns: A sha256 hex digest for the file.
    """
    with path.open("rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


class AppPackagesMergeMixin:
    # A mixin containing the utilities to merge independent platform-specific app_packages folders
    # into a single "fat" app_packages folder. This is currently only used by macOS, but it *could*
    # be required on iOS if they ever re-introduce multiple on-device architectures.

    def find_binary_packages(
        self,
        install_path: Path,
        universal_suffix: str = None,
    ) -> list[tuple[str, str]]:
        """Find the packages that have been installed that have binary components.

        :param install_path: The path into which packages have been installed.
        :param universal_suffix: The tag suffix that indicates a universal wheel.
        :returns: A list of (package name, version) tuples, describing the packages that
            are in the install path that are non-universal and non-pure.
        """
        binary_packages = []
        for distinfo in install_path.glob("*.dist-info"):
            # Read the WHEEL file in the dist-info folder.
            # Use this to determine if the wheel is "pure", and the tag
            # for the wheel.
            with (distinfo / "WHEEL").open("r", encoding="utf-8") as f:
                wheel_data = email.message_from_string(f.read())
                is_purelib = wheel_data.get("Root-Is-Purelib", "false") == "true"
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

    def ensure_thin_binary(self, path: Path, arch: str):
        """Ensure that a binary is thin, targeting a given architecture.

        If the library is already thin, it is left as-is.

        :param path: The library file to process.
        :param arch: The architecture that should be preserved.
        """
        try:
            output = self.tools.subprocess.check_output(
                ["lipo", "-info", path],
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to inspect architectures in {path}"
            ) from e
        else:
            if output.startswith("Non-fat file: "):
                self.logger.verbose(f"{path} is already thin.")
            elif output.startswith("Architectures in the fat file: "):
                architectures = set(output.strip().split(":")[-1].strip().split(" "))
                if arch in architectures:
                    self.logger.verbose(f"Thinning {path}")
                    try:
                        thin_lib_path = path.parent / f"{path.name}.{arch}"
                        self.tools.subprocess.run(
                            [
                                "lipo",
                                "-thin",
                                arch,
                                "-output",
                                thin_lib_path,
                                path,
                            ],
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        raise BriefcaseCommandError(
                            f"Unable to create thin binary from {path}"
                        ) from e
                    else:
                        # Having extracted the single architecture into a temporary
                        # file, replace the original with the thin version.
                        self.tools.shutil.move(thin_lib_path, path)
                else:
                    raise BriefcaseCommandError(
                        f"{path} does not contain a {arch} slice."
                    )
            else:
                raise BriefcaseCommandError(
                    f"Unable to determine architectures in {path}"
                )

    def lipo_dylib(self, relative_path: Path, target_path: Path, sources: list[Path]):
        """Create a fat library by invoking lipo on multiple source libraries.

        :param relative_path: The path fragment for the dylib, relative to the root
        :param target_path: The root location where the fat library will be written
        :param sources: A list of root locations providing single platform libraries.
        """
        self.logger.verbose(f"Creating fat library {relative_path}")

        try:
            # Ensure the directory where the library will be written exists.
            (target_path / relative_path).parent.mkdir(exist_ok=True, parents=True)

            # Add all the constructed source paths. If the original binary is universal,
            # or the binary is only needed on *some* platforms (e.g., libjpeg isn't
            # included in the x86_64 Pillow wheel), the source won't exist, so only
            # merge sources that actually exist. lipo allows creating a "fat"
            # single-platform binary; it's effectively a copy.
            self.tools.subprocess.run(
                [
                    "lipo",
                    "-create",
                    "-output",
                    target_path / relative_path,
                ]
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

    def thin_app_packages(
        self,
        app_packages: Path,
        arch: str,
    ):
        """Ensure that all the dylibs in a given app_packages folder are thin."""
        dylibs = []
        for source_path in app_packages.glob("**/*"):
            if source_path.suffix in {".so", ".dylib"}:
                dylibs.append(source_path)

        # Call lipo on each dylib that was found to ensure it is thin.
        if dylibs:
            # Do this in a threadpool to make it run faster.
            progress_bar = self.input.progress_bar()
            self.logger.info(f"Thinning libraries in {app_packages.name}...")
            task_id = progress_bar.add_task("Create fat libraries", total=len(dylibs))
            with progress_bar:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for path in dylibs:
                        future = executor.submit(
                            self.ensure_thin_binary,
                            path=path,
                            arch=arch,
                        )
                        futures.append(future)
                    for future in concurrent.futures.as_completed(futures):
                        progress_bar.update(task_id, advance=1)
                        if future.exception():
                            raise future.exception()
        else:
            self.logger.info("No libraries require thinning.")

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

        # Copy all the non-library files from the source to the target. If a file exists
        # in multiple sources, do a checksum, and warn if there is a discrepancy. If
        # there is a discrepancy, the version from the first source is what will be
        # used. Don't warn if the file is in a __pycache__ folder; these will always be
        # different, but they'll be purged later anyway. Don't warn for anything in a
        # .dist-info folder either; these are going to be different because of platform
        # difference, but core package metadata should be consistent.
        dylibs = set()
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
                            dylibs.add(relative_path)
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
                            # The file doesn't exist yet; copy it as is (including
                            # permissions), and store the digest for later comparison
                            self.tools.shutil.copy(source_path, target_path)
                            digests[relative_path] = sha256_file_digest(source_path)

        # Call lipo on each dylib that was found to create the fat version.
        if dylibs:
            # Do this in a threadpool to make it run faster.
            progress_bar = self.input.progress_bar()
            self.logger.info("Merging libraries...")
            task_id = progress_bar.add_task("Create fat libraries", total=len(dylibs))
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
        else:
            self.logger.info("No libraries require merging.")
