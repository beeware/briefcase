from email.message import Message
from urllib.parse import urlparse

import requests.exceptions as requests_exceptions

from briefcase.exceptions import (
    BadNetworkResourceError,
    MissingNetworkResourceError,
    NetworkFailure,
)


class Download:
    def __init__(self, tools):
        self.tools = tools

    @classmethod
    def verify(cls, tools):
        """Make downloader available in tool cache."""
        # short circuit since already verified and available
        if hasattr(tools, "download"):
            return tools.download

        tools.download = Download(tools=tools)
        return tools.download

    def file(self, url, download_path, role=None):
        """Download a given URL, caching it. If it has already been downloaded,
        return the value that has been cached.

        This is a utility method used to obtain assets used by the
        install process. The cached filename will be the filename portion of
        the URL, appended to the download path.

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
                # We have meaningful content, and it hasn't been cached previously,
                # so save it in the requested location
                self.tools.logger.info(f"Downloading {cache_name}...")
                with filename.open("wb") as f:
                    total = response.headers.get("content-length")
                    if total is None:
                        f.write(response.content)
                    else:
                        progress_bar = self.tools.input.progress_bar()
                        task_id = progress_bar.add_task("Downloader", total=int(total))
                        with progress_bar:
                            for data in response.iter_content(chunk_size=1024 * 1024):
                                f.write(data)
                                progress_bar.update(task_id, advance=len(data))

        except requests_exceptions.ConnectionError as e:
            if role:
                description = role
            else:
                description = filename.name if filename else url
            raise NetworkFailure(f"download {description}") from e

        return filename
