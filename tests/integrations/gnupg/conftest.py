import pytest

from briefcase.integrations.gnupg import GnuPG


@pytest.fixture
def gpg(mock_tools):
    mock_tools.host_os = "Linux"
    return GnuPG(tools=mock_tools)


JANE = "5F0B07E0E2D05DD5611BF7A3F9FCBC4A7701B685"
BOB = "B6C8B38C96FFE1E6A1C66C9F4D68E1A93D2F47FB"

GPG_OUTPUT = "\n".join(
    [
        "sec:u:255:22:F9FCBC4A7701B685:1785485940:::u:::scSC:::+::ed25519:::0:",
        f"fpr:::::::::{JANE}:",  # codespell:ignore fpr
        "grp:::::::::A93A9F4A002A4796BB0196F46C2ED4F603F95854:",
        "uid:u::::1785485940::E70814C3C8DC3AC3940E8BFBA0288F0CE55F2120::Jane Doe <jane@example.com>::::::::::0:",
        "ssb:u:255:22:5B0C17E0E2D05DD5611BF7A3F9FCBC4A7701B685:1785485940:::u:::e:::+::ed25519:::0:",
        "fpr:::::::::5B0C17E0E2D05DD5611BF7A3F9FCBC4A7701B685:",  # codespell:ignore fpr
    ]
)
GPG_OUTPUT += "\n"

BOB_OUTPUT = "\n".join(
    [
        "sec:u:3072:1:4D68E1A93D2F47FB:1785485980:::u:::scESC:::::::",
        f"fpr:::::::::{BOB}:",  # codespell:ignore fpr
        "uid:u::::1785485980::89A2D4C6E5F8B3E7::Bob Builder <bob@example.com>::::::::::0:",
    ]
)
BOB_OUTPUT += "\n"

JANE_ALT_UID = (
    "uid:u::::1785485940::E70814C3C8DC3AC3940E8BFBA0288F0CE55F2120::"
    "Jane's secret alternate identity <jane@example.com>::::::::::0:\n"
)
