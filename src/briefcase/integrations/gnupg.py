from __future__ import annotations

import subprocess

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
        except OSError:
            # gpg isn't installed.
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
