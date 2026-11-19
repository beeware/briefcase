from __future__ import annotations

import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache


class GnuPG(Tool):
    name = "gnupg"
    full_name = "GNU Privacy Guard"

    @classmethod
    def verify_install(cls, tools: ToolCache, **kwargs) -> GnuPG:
        """Verify that GnuPG is installed and available.

        :param tools: ToolCache of available tools
        :returns: A wrapper for the GnuPG tools.
        """
        # short circuit since already verified and available
        if hasattr(tools, "gnupg"):
            return tools.gnupg

        gpg = GnuPG(tools=tools)
        try:
            tools.subprocess.check_output(["gpg", "--version"], quiet=1)
        except OSError as e:
            raise BriefcaseCommandError(
                "Can't find the gpg tool. Install the `gnupg` package for your "
                "operating system, and try again."
            ) from e
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Unable to invoke gpg.") from e

        tools.gnupg = gpg
        return gpg

    def identities(self) -> dict[str, str]:
        """Obtain a set of valid GPG signing identities.

        :returns: A dictionary of the GPG signing identities available on the system,
            keyed by fingerprint, with the primary user ID as the value.
        """
        try:
            output = self.tools.subprocess.check_output(
                ["gpg", "--list-secret-keys", "--with-colons"],
                quiet=1,
            )
        except subprocess.CalledProcessError:
            # gpg returns a non-zero exit code when no secret keys are available.
            return {}

        identities = {}
        fingerprint = None
        for line in output.split("\n"):
            record = line.split(":")
            if record[0] == "sec":
                # A new secret key; the fingerprint of the key will follow.
                fingerprint = None
            elif record[0] == "fpr":  # codespell:ignore fpr
                # The fingerprint of the current secret key. The first UID for the
                # key is used as the identity name.
                if fingerprint is None:
                    fingerprint = record[9]
            elif record[0] == "uid" and fingerprint and fingerprint not in identities:
                identities[fingerprint] = record[9]

        return identities

    def export_public_key(self, identity: str, output_path: Path):
        """Export the public key for an identity to a file.

        The exported public key can be imported into a different environment (e.g., a
        Docker container) so that it can be associated with the secret key held by the
        host's GPG agent.

        :param identity: The fingerprint of the identity to export
        :param output_path: The path of the file to write the exported key to
        """
        try:
            self.tools.subprocess.run(
                [
                    "gpg",
                    "--batch",
                    "--output",
                    output_path,
                    "--export",
                    identity,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Error exporting the GPG public key for identity {identity}."
            ) from e

    def agent_socket_path(self) -> Path:
        """Return the path of the host's GPG agent socket.

        :returns: The path of the socket used to communicate with the GPG agent.
        """
        try:
            socket_path = self.tools.subprocess.check_output(
                ["gpgconf", "--list-dirs", "agent-socket"],
                quiet=1,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as e:
            raise BriefcaseCommandError(
                "Can't determine the path of the GPG agent socket. Ensure that "
                "gpgconf is installed and the GPG agent is running."
            ) from e
        return Path(socket_path)
