from unittest import mock


def test_no_source(create_command, tmp_path):
    "If the app doesn't define a source, no image is installed"
    create_command.shutil = mock.MagicMock()

    # Try to install the image from no source.
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        source=None,
        target=out_path
    )

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_no_source_with_size(create_command, tmp_path):
    "If the app doesn't define a source, and a size is requested, no image is installed"
    create_command.shutil = mock.MagicMock()

    # Try to install the image from no source.
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='3742',
        source=None,
        target=out_path
    )

    # No file was installed.
    create_command.shutil.copy.assert_not_called()


def test_no_requested_size(create_command, tmp_path, capsys):
    "If the app specifies a no-size image, an un-annotated image is used."
    create_command.shutil = mock.MagicMock()

    # Create the source image
    source_file = tmp_path / 'input' / 'original.png'
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open('w') as f:
        f.write('image')

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        source='input/original',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Installing input/original.png as sample image...\n"

    # The file was copied into position
    create_command.shutil.copy.assert_called_with(
        str(create_command.base_path / 'input' / 'original.png'),
        str(out_path),
    )


def test_no_requested_size_invalid_path(create_command, tmp_path, capsys):
    "If the app specifies an no-size image that doesn't exist, an error is raised."
    create_command.shutil = mock.MagicMock()
    create_command.shutil.copy.side_effect = FileNotFoundError

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size=None,
        source='input/original',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == (
        "Unable to find input/original.png for sample image; using default\n"
    )

    # The file was not copied
    assert create_command.shutil.copy.call_count == 0


def test_requested_size(create_command, tmp_path, capsys):
    "If the app specifies a sized image, an anoated image filename is used."
    create_command.shutil = mock.MagicMock()

    # Create the source image
    source_file = tmp_path / 'input' / 'original-3742.png'
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open('w') as f:
        f.write('image')

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='3742',
        source='input/original',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == "Installing input/original-3742.png as 3742px sample image...\n"

    # The file was copied into position
    create_command.shutil.copy.assert_called_with(
        str(create_command.base_path / 'input' / 'original-3742.png'),
        str(out_path),
    )


def test_requested_size_invalid_path(create_command, tmp_path, capsys):
    "If the app specifies an sized image that doesn't exist, an error is raised."
    create_command.shutil = mock.MagicMock()
    create_command.shutil.copy.side_effect = FileNotFoundError

    # Try to install the image
    out_path = tmp_path / 'output.png'
    create_command.install_image(
        'sample image',
        size='3742',
        source='input/original',
        target=out_path
    )

    # The right message was written to output
    assert capsys.readouterr().out == (
        "Unable to find input/original-3742.png for 3742px sample image; using default\n"
    )

    # The file was not copied
    assert create_command.shutil.copy.call_count == 0
