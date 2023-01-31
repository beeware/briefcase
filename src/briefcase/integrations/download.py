import os
import tempfile
from contextlib import suppress
from email.message import Message
from urllib.parse import urlparse

import requests.exceptions as requests_exceptions

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError,
    NetworkFailure,
)
from briefcase.integrations.base import Tool, ToolCache


class Download(Tool):
    name = "download"
    full_name = "Download"

    def __init__(self, tools: ToolCache):
        self.tools = tools

    @classmethod
    def verify(cls, tools: ToolCache):
        """Make downloader available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "download"):
            return tools.download

        tools.download = Download(tools=tools)
        return tools.download

    def file(self, url, download_path, role=None):
        """Download a given URL, caching it. If it has already been downloaded, return
        the value that has been cached.

        This is a utility method used to obtain assets used by the installation
        process. The cached filename will be the filename portion of the URL,
        appended to the download path.

        :param url: The URL to download
        :param download_path: The path to the download cache folder. This path
            will be created if it doesn't exist.
        :param role: A string describing the role played by the file being
            downloaded; used to construct log and error messages. Should be
            able to fit into the sentence "Error downloading {role}".
        :returns: The filename of the downloaded (or cached) file.
        """
        download_path.mkdir(parents=True, exist_ok=True)
        filename = None
        try:
            response = self.tools.requests.get(url, stream=True)
            if response.status_code == 404:
                raise MissingNetworkResourceError(url=url)
            elif response.status_code != 200:
                raise BadNetworkResourceError(url=url, status_code=response.status_code)

            # The initial URL might (read: will) go through URL redirects, so
            # we need the *final* response. We look at either the `Content-Disposition`
            # header, or the final URL, to extract the cache filename.
            cache_full_name = urlparse(response.url).path
            header_value = response.headers.get("Content-Disposition")
            if header_value:
                # Neither requests nor httplib provides a way to parse RFC6266 headers.
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
                self.tools.logger.info(f"{cache_name} already downloaded")
            else:
                self.tools.logger.info(f"Downloading {cache_name}...")
                self._fetch_and_write_content(response, filename)
        except requests_exceptions.ConnectionError as e:
            if role:
                description = role
            else:
                description = filename.name if filename else url
            raise NetworkFailure(f"download {description}") from e

        return filename

    def _fetch_and_write_content(self, response, filename):
        """Write the content from the requests Response to file.

        The data is initially written in to a temporary file in the Briefcase
        cache. This avoids partially downloaded files masquerading as complete
        downloads in later Briefcase runs. The temporary file is only moved
        to ``filename`` if the download is successful; otherwise, it is deleted.

        :param response: ``requests.Response``
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
                    temp_file.write(response.content)
                else:
                    progress_bar = self.tools.input.progress_bar()
                    task_id = progress_bar.add_task("Downloader", total=int(total))
                    with progress_bar:
                        for data in response.iter_content(chunk_size=1024 * 1024):
                            temp_file.write(data)
                            progress_bar.update(task_id, advance=len(data))

            # This file move short circuits to a file rename when the source and
            # destination are on the same filesystem; therefore, it should complete
            # quite quickly even for large files.
            self.tools.shutil.move(temp_file.name, filename)
            # Temporary files are created with only read/write permissions for the
            # file's owner (i.e. 600); to match the behavior of file creation using
            # ``open(..., w)``, the downloaded file's permissions are updated for
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
