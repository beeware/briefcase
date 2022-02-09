from random import randrange
from pathlib import Path

PATCH = {
    'offset': 0x08,
    'original': bytes.fromhex('414902'),
    'patch': bytes.fromhex('000000')
}


def create_mock_appimage(appimage_path: Path, mock_appimage_kind: str = 'original'):
    """
    Create a mock AppImage for testing purposes.

    Args:
        appimage_path (Path): Path to the appimage to create.
        mock_appimage_kind (str): The kind of mock appimage to create.
            'original' creates an unpatched mock appimage.
            'patched' creates a patched mock appimage.
            'corrupt' creates a corrupted mock appimage.

    Returns:
        bytes_to_be_patched (bytes): The bytes to be patched of the created AppImage.
    """

    bytes_to_be_patched = None

    appimage_headers = {
        'original': bytes.fromhex('7f454c46020101004149020000000000'),
        'patched': bytes.fromhex('7f454c46020101000000000000000000'),
        'corrupt': bytes.fromhex('%030x' % randrange(16**30))
    }

    appimage_path.touch()
    with open(appimage_path, 'w+b') as mock_appimage:
        if mock_appimage_kind in appimage_headers:
            mock_appimage.write(appimage_headers[mock_appimage_kind])
        else:
            raise ValueError(f'Unknown mock_appimage_kind: {mock_appimage_kind}')
        mock_appimage.seek(PATCH['offset'])
        bytes_to_be_patched = mock_appimage.read(len(PATCH['original']))

    return bytes_to_be_patched
