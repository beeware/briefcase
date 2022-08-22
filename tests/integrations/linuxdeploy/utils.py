from pathlib import Path
from random import randrange

from briefcase.integrations.linuxdeploy import (
    ELF_PATCH_OFFSET,
    ELF_PATCH_ORIGINAL_BYTES,
)


def create_mock_appimage(appimage_path: Path, mock_appimage_kind: str = "original"):
    """Create a mock AppImage for testing purposes.

    :param appimage_path: Path to the appimage to create.
    :param mock_appimage_kind: The kind of mock appimage to create.
            'original' creates an unpatched mock appimage.
            'patched' creates a patched mock appimage.
            'corrupt' creates a corrupted mock appimage.

    :returns: The bytes to be patched of the created AppImage.
    """

    bytes_to_be_patched = None

    appimage_headers = {
        "original": bytes.fromhex("7f454c46020101004149020000000000"),
        "patched": bytes.fromhex("7f454c46020101000000000000000000"),
        "corrupt": bytes.fromhex("%030x" % randrange(16**30)),
        "empty": b"",
    }

    appimage_path.parent.mkdir(parents=True, exist_ok=True)
    appimage_path.touch()
    with open(appimage_path, "w+b") as mock_appimage:
        if mock_appimage_kind in appimage_headers:
            mock_appimage.write(appimage_headers[mock_appimage_kind])
        else:
            raise ValueError(f"Unknown mock_appimage_kind: {mock_appimage_kind}")
        mock_appimage.seek(ELF_PATCH_OFFSET)
        bytes_to_be_patched = mock_appimage.read(len(ELF_PATCH_ORIGINAL_BYTES))

    return bytes_to_be_patched


def side_effect_create_mock_appimage(appimage_path):
    """A test fixture side effect that creates an AppImage at the specified
    path."""

    def _side_effect(*args, **kwargs):
        create_mock_appimage(appimage_path=appimage_path)
        return "new-downloaded-file"

    return _side_effect


def side_effect_create_mock_tool(tool_path):
    """A test fixture side effect that creates an sh file at the specified
    path."""

    def _side_effect(*args, **kwargs):
        tool_path.parent.mkdir(parents=True)
        with tool_path.open("w") as f:
            f.write("I am a complete tool")
        return "new-downloaded-file"

    return _side_effect
