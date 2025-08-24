from __future__ import annotations

import itertools
import os
import shutil
import ssl
import sys
import tempfile
from collections.abc import Iterable, Sequence
from contextlib import suppress
from email.message import Message
from pathlib import Path

import httpx
import truststore

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError,
    NetworkFailure,
)
from briefcase.integrations.base import Tool, ToolCache


class File(Tool):
    name = "file"
    full_name = "File"

    @classmethod
    def verify_install(cls, tools: ToolCache, **kwargs) -> File:
        """Make File available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "file"):
            return tools.file

        tools.file = File(tools=tools)
        return tools.file

    @classmethod
    def sorted_depth_first(cls, paths: Sequence[Path]) -> Iterable[Path]:
        """Sort a list of paths, so that they appear in lexical order, with
        subdirectories of a folder sorting before files in the same directory.

        :param paths: The list of paths to sort.
        :returns: The sorted list of paths
        """
        # The sort key for a path is a triple - the parent of the path; whether the path
        # is a directory or not; and finally, the actual path. We then sort this in
        # reverse order.
        #
        # Sorting by the parent of the path first (in reverse order) guarantees that
        # long paths are sorted first; so a file in a folder will come *after* the
        # folder it is in.
        #
        # The second term (parent.is_dir()) guarantees that subfolders in a folder are
        # found before files in the same folder (because in reverse order, booleans sort
        # True before False).
        #
        # Lastly, we sort on the actual path itself. This provide a guaranteed lexical
        # ordering inside any given folder. This isn't strictly required, but it's
        # helpful for testing and reproducibility that the sort order is reliable and
        # repeatable.
        return sorted(paths, key=lambda p: (p.parent, p.is_dir(), p), reverse=True)

    @classmethod
    def sorted_depth_first_groups(
        cls,
        paths: Sequence[Path],
    ) -> Iterable[Iterable[Path]]:
        """Convert a list of paths into a collection of groups that are all at the same
        "level", grouped depth-first.

        Subfolders in a folder will be in a separate group, returned *before* files in
        the same folder.

        :param paths: The list of paths return grouped.
        :returns: A generator returning a iterable groups of paths that are all at the
            same sorting level.
        """
        # The sort function guarantees depth first ordering, with folders before files
        # at the same level.
        #
        # The grouping key is based on the parent of the path (so that all objects in
        # the same folder group together), with an additional discriminator to ensure
        # that subfolders are in a different group to files.
        #
        # itertools.groupby guarantees a new group whenever the key changes; and the
        # input sort order guarantees that directories come before files, so we get
        # our desired sort grouping and ordering.
        return (
            group_paths
            for _, group_paths in itertools.groupby(
                cls.sorted_depth_first(paths),
                lambda path: (path.parent, path.is_dir()),
            )
        )

    @property
    def ssl_context(self):
        """The SSL context to use for downloads."""
        try:
            return self._ssl_context
        except AttributeError:
            self._ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

            return self._ssl_context

    def is_archive(self, filename: str | os.PathLike) -> bool:
        """Can a file be unpacked via `shutil.unpack_archive()`?

        The evaluation is based purely on the name of the file. A more robust
        implementation may actually interrogate the file itself.

        Notably, the types of archives that can be unpacked will vary based on the types
        of compression the current Python supports. So, for example, if LZMA is not
        available, then tar.xz archives cannot be unpacked.

        :param filename: path to file to evaluate as an archive
        """
        filename = Path(filename)
        file_extensions = {
            # captures extensions like .tar.gz, .tar.bz2, etc.
            "".join(filename.suffixes[-2:]),
            # as well as .tar, .zip, etc.
            filename.suffix,
        }
        return not file_extensions.isdisjoint(self.supported_archive_extensions)

    @property
    def supported_archive_extensions(self) -> set[str]:
        return {
            extension
            for archive_format in shutil.get_unpack_formats()
            for extension in archive_format[1]
        }

    def unpack_archive(
        self,
        filename: str | os.PathLike,
        extract_dir: str | os.PathLike,
        **kwargs,
    ):
        """Unpack an archive file in to a destination directory.

        Additional protections for unpacking tar files were introduced in Python 3.12.
        Since tarballs can contain anything valid in a UNIX file system, these
        protections prevent unpacking potentially dangerous files. This behavior will be
        the default in Python 3.14. However, the protections can only be enabled for tar
        files...not zip files.

        :param filename: File path for the archive
        :param extract_dir: Target file path for where to unpack archive
        :param kwargs: additional arguments for shutil.unpack_archive
        """
        is_zip = Path(filename).suffix == ".zip"
        if sys.version_info >= (3, 12):  # pragma: no-cover-if-lt-py312
            unpack_kwargs = {"filter": "data"} if not is_zip else {}
        else:  # pragma: no-cover-if-gte-py312
            unpack_kwargs = {}

        self.tools.shutil.unpack_archive(
            filename=filename,
            extract_dir=extract_dir,
            **{
                **unpack_kwargs,
                **kwargs,
            },
        )

    def download(self, url: str, download_path: Path, role: str | None = None) -> Path:
        """Download a given URL, caching it. If it has already been downloaded, return
        the value that has been cached.

        This is a utility method used to obtain assets used by the installation process.
        The cached filename will be the filename portion of the URL, appended to the
        download path.

        :param url: The URL to download
        :param download_path: The path to the download cache folder. This path will be
            created if it doesn't exist.
        :param role: A string describing the role played by the file being downloaded;
            used to construct log and error messages. Should be able to fit into the
            sentence "Error downloading {role}".
        :returns: The filename of the downloaded (or cached) file.
        """
        download_path.mkdir(parents=True, exist_ok=True)
        filename: Path = None
        try:
            with self.tools.httpx.stream(
                "GET",
                url,
                follow_redirects=True,
                verify=self.ssl_context,
            ) as response:
                if response.status_code == 404:
                    raise MissingNetworkResourceError(url=url)
                elif response.status_code != 200:
                    raise BadNetworkResourceError(
                        url=url, status_code=response.status_code
                    )

                # The initial URL might (read: will) go through URL redirects, so
                # we need the *final* response. We look at either the `Content-Disposition`
                # header, or the final URL, to extract the cache filename.
                cache_full_name = response.url.path
                header_value = response.headers.get("Content-Disposition")
                if header_value:
                    # Httpx does not provide a way to parse RFC6266 headers.
                    # The cgi module *did* have a way to parse these headers, but
                    # it was deprecated as part of PEP594. PEP594 recommends
                    # using the email.message module to parse these headers as they
                    # are near identical format.
                    # See also:
                    # * https://tools.ietf.org/html/rfc6266
                    # * https://peps.python.org/pep-0594/#cgi
                    msg = Message()
                    msg["Content-Disposition"] = header_value
                    filename = msg.get_filename()
                    if filename:
                        cache_full_name = filename
                cache_name = cache_full_name.split("/")[-1]
                filename = download_path / cache_name

                if filename.exists():
                    self.tools.console.info(f"{cache_name} already downloaded")
                else:
                    self.tools.console.info(f"Downloading {cache_name}...")
                    self._fetch_and_write_content(response, filename)
        except httpx.RequestError as e:
            if role:
                description = role
            else:
                description = filename.name if filename else url

            if isinstance(e, httpx.TooManyRedirects):
                # httpx, unlike requests, will not follow redirects indefinitely, and defaults to
                # 20 redirects before calling it quits. If the download attempt exceeds 20 redirects,
                # Briefcase probably needs to re-evaluate the URLs it is using for that download
                # and ideally find a starting point that won't have so many redirects.
                hint = "exceeded redirects when downloading the file.\n\nPlease report this as a bug to Briefcase."
            elif isinstance(e, httpx.DecodingError):
                hint = "the server sent a malformed response."
            elif isinstance(e, httpx.ConnectError):
                try:
                    # It's a little difficult to verify exactly what might cause httpx
                    # to raise a ConnectError, but `__context__.__context__` should be
                    # an SSLCertVerificationError if there's a certificate problem.
                    # Catch that case, and print the raw exception in other cases.
                    context = e.__context__.__context__
                except AttributeError:
                    context = None

                if isinstance(context, ssl.SSLCertVerificationError):
                    hint = (
                        "a connection to the server could not be established due to "
                        "a certificate verification problem.\n\n"
                        "This probably indicates an issue with a proxy configuration "
                        "on your computer."
                    )
                else:
                    hint = (
                        "a connection to the server could not be established.\n\n"
                        f"The reported cause of the problem was {e}"
                    )
            else:
                # httpx.TransportError
                # Use the default hint for generic network communication errors
                hint = (
                    "is your computer offline?\n\n"
                    f"The reported cause of the problem was {e}"
                )

            raise NetworkFailure(
                f"download {description}",
                hint,
            ) from e

        return filename

    def _fetch_and_write_content(self, response: httpx.Response, filename: Path):
        """Write the content from the httpx Response to file.

        The data is initially written in to a temporary file in the Briefcase
        cache. This avoids partially downloaded files masquerading as complete
        downloads in later Briefcase runs. The temporary file is only moved
        to ``filename`` if the download is successful; otherwise, it is deleted.

        :param response: ``httpx.Response``
        :param filename: full filesystem path to save data
        """
        temp_file = tempfile.NamedTemporaryFile(
            dir=filename.parent,
            prefix=f"{filename.name}.",
            suffix=".download",
            delete=False,
        )
        try:
            with temp_file:
                total = response.headers.get("content-length")
                if total is None:
                    response.read()
                    temp_file.write(response.content)
                else:
                    progress_bar = self.tools.console.progress_bar()
                    task_id = progress_bar.add_task("Downloader", total=int(total))
                    with progress_bar:
                        for data in response.iter_bytes(chunk_size=1024 * 1024):
                            temp_file.write(data)
                            progress_bar.update(task_id, advance=len(data))

            # This file move short circuits to a file rename when the source and
            # destination are on the same filesystem; therefore, it should complete
            # quite quickly even for large files.
            self.tools.shutil.move(temp_file.name, filename)
            # Temporary files are created with only read/write permissions for the
            # file's owner (i.e. 600); to match the behavior of file creation using
            # ``open(..., "w")``, the downloaded file's permissions are updated for
            # the group and world to have read/write permissions as well. Finally,
            # (as with ``open()``) the system's umask is respected. The current
            # umask is only available as the return value to updating the umask...
            # Updating the umask affects the current process, including all threads.
            # A umask value represents permissions that should be denied; so, 022
            # denies write permissions to the group and world. A 022 umask is a
            # common default among supporting systems.
            os.umask(current_umask := os.umask(0o022))
            # The umask is applied by inverting it and bitwise ANDing the default
            # permissions...thus masking out permissions that should be denied.
            self.tools.os.chmod(filename, 0o666 & ~current_umask)
        finally:
            # Ensure the temporary file is deleted; this file may still
            # exist if the download fails or the user sends CTRL+C.
            with suppress(FileNotFoundError):
                self.tools.os.remove(temp_file.name)
