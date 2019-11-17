from unittest import mock


def test_no_sources(create_command, tmp_path, capsys):
    "If the app doesn't define any sources, no image is installed"
    create_command.shutil = mock.MagicMock()

    # Try to install the image from no source.
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        sources=None,
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "No sample image defined in app config; using default\n"

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_no_sources_with_size(create_command, tmp_path, capsys):
    "If the app doesn't define any sources, and a size is requested, no image is installed"
    create_command.shutil = mock.MagicMock()

    # Try to install the image from no source.
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='3742',
        sources=None,
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "No 3742px sample image defined in app config; using default\n"

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_simple_source_no_requested_size(create_command, tmp_path, capsys):
    "If the app specifies a single image, but no size, the image is used as-is."
    create_command.shutil = mock.MagicMock()

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        sources='input/original.png',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Installing sample image...\n"

    # The file was copied into position
    create_command.shutil.copy.assert_called_with(
        create_command.base_path / 'input' / 'original.png',
        out_path,
    )


def test_simple_source_no_requested_size_invalid_path(create_command, tmp_path, capsys):
    "If the app specifies a single image, but no size, the image is used as-is."
    create_command.shutil = mock.MagicMock()
    create_command.shutil.copy.side_effect = FileNotFoundError

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        sources='input/original.png',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == (
        "Installing sample image...\n"
        "Unable to find input/original.png specified for sample image; using default\n"
    )

    # The file was copied into position
    create_command.shutil.copy.assert_called_with(
        create_command.base_path / 'input' / 'original.png',
        out_path,
    )


def test_simple_source_no_requested_size_format_mismatch(create_command, tmp_path, capsys):
    "If you provide a single image, but no size, and the file format doesn't match, don't install"
    create_command.shutil = mock.MagicMock()

    # Try to install the image from no source.
    # The provide image is a jpg, not a png.
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        sources='input/original.jpg',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Sample image requires a .png (.jpg provided); using default\n"

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_simple_source_requested_size(create_command, tmp_path, capsys):
    "If the app specifies a size, a single source image can't be used."
    create_command.shutil = mock.MagicMock()

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='3742',
        sources='input/original.png',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Sample image requires a 3742px .png; using default\n"

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_multiple_sources_with_size_match(create_command, tmp_path, capsys):
    "If one of the source images matches the requested size, it will be used"
    create_command.shutil = mock.MagicMock()

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='37',
        sources={
            '37': 'input/original-37.png',
            '42': 'input/original-42.png',
        },
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Installing 37px sample image...\n"

    # The file of the right size was copied into position
    create_command.shutil.copy.assert_called_with(
        create_command.base_path / 'input' / 'original-37.png',
        out_path,
    )


def test_multiple_sources_with_size_match_invalid_file(create_command, tmp_path, capsys):
    "If the file matching the requested size doesn't exist, fall back to default"
    create_command.shutil = mock.MagicMock()
    create_command.shutil.copy.side_effect = FileNotFoundError

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='37',
        sources={
            '37': 'input/original-37.png',
            '42': 'input/original-42.png',
        },
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == (
        "Installing 37px sample image...\n"
        "Unable to find input/original-37.png specified for 37px sample image; using default\n"
    )

    # The file of the right size was copied into position
    create_command.shutil.copy.assert_called_with(
        create_command.base_path / 'input' / 'original-37.png',
        out_path,
    )


def test_multiple_sources_with_size_match_format_mismatch(create_command, tmp_path, capsys):
    "If there is a size match, but a format mismatch, fall back to the default image"
    create_command.shutil = mock.MagicMock()

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='37',
        sources={
            '37': 'input/original-37.jpg',
            '42': 'input/original-42.png',
        },
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Sample image requires a 37px .png (.jpg provided); using default\n"

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_mutliple_sources_with_no_size_match(create_command, tmp_path, capsys):
    "If there's no size match in the source images, fall back to default"
    create_command.shutil = mock.MagicMock()

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='123',
        sources={
            '37': 'input/original-37.png',
            '42': 'input/original-42.png',
        },
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Sample image requires a 123px .png; using default\n"

    # No file was installed.
    create_command.shutil.copy.assert_not_called()
