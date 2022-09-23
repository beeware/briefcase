import shutil
from unittest import mock


def test_no_source(create_command, tmp_path):
    """If the app doesn't define a source, no image is installed."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Try to install the image from no source.
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source=None,
        variant=None,
        size=None,
        target=out_path,
    )

    # No file was installed.
    create_command.tools.shutil.copy.assert_not_called()


def test_no_source_with_size(create_command, tmp_path):
    """If the app doesn't define a source, and a size is requested, no image is
    installed."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Try to install the image from no source.
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source=None,
        variant=None,
        size="3742",
        target=out_path,
    )

    # No file was installed.
    create_command.tools.shutil.copy.assert_not_called()


def test_no_requested_size(create_command, tmp_path, capsys):
    """If the app specifies a no-size image, an un-annotated image is used."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source="input/original",
        variant=None,
        size=None,
        target=out_path,
    )

    # The right message was written to output
    expected = "Installing input/original.png as sample image... done\n\n"
    assert capsys.readouterr().out == expected

    # The file was copied into position
    create_command.tools.shutil.copy.assert_called_with(
        create_command.base_path / "input" / "original.png",
        out_path,
    )


def test_no_requested_size_invalid_path(create_command, tmp_path, capsys):
    """If the app specifies a no-size image that doesn't exist, an error is
    raised."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.copy.side_effect = FileNotFoundError

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source="input/original",
        variant=None,
        size=None,
        target=out_path,
    )

    # The right message was written to output
    expected = "Unable to find input/original.png for sample image; using default\n"
    assert capsys.readouterr().out == expected

    # The file was not copied
    assert create_command.tools.shutil.copy.call_count == 0


def test_requested_size(create_command, tmp_path, capsys):
    """If the app specifies a sized image, an annotated image filename is
    used."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original-3742.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source="input/original",
        variant=None,
        size="3742",
        target=out_path,
    )

    # The right message was written to output
    expected = "Installing input/original-3742.png as 3742px sample image... done\n\n"
    assert capsys.readouterr().out == expected

    # The file was copied into position
    create_command.tools.shutil.copy.assert_called_with(
        create_command.base_path / "input" / "original-3742.png",
        out_path,
    )


def test_requested_size_invalid_path(create_command, tmp_path, capsys):
    """If the app specifies a sized image that doesn't exist, an error is
    raised."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.copy.side_effect = FileNotFoundError

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source="input/original",
        variant=None,
        size="3742",
        target=out_path,
    )

    # The right message was written to output
    expected = "Unable to find input/original-3742.png for 3742px sample image; using default\n"
    assert capsys.readouterr().out == expected

    # The file was not copied
    assert create_command.tools.shutil.copy.call_count == 0


def test_variant_with_no_requested_size(create_command, tmp_path, capsys):
    """If the app specifies a variant with no size, the variant is used
    unsized."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source={
            "round": "input/original",
        },
        variant="round",
        size=None,
        target=out_path,
    )

    # The right message was written to output
    expected = "Installing input/original.png as round sample image... done\n\n"
    assert capsys.readouterr().out == expected

    # The file was copied into position
    create_command.tools.shutil.copy.assert_called_with(
        create_command.base_path / "input" / "original.png",
        out_path,
    )


def test_variant_without_variant_source_and_no_requested_size(
    create_command, tmp_path, capsys
):
    """If the template specifies a variant with no size, but app doesn't have
    variants, a message is reported."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source="input/original",
        variant="round",
        size=None,
        target=out_path,
    )

    # The right message was written to output
    expected = "Unable to find round variant for sample image; using default\n"
    assert capsys.readouterr().out == expected

    # No file was installed.
    create_command.tools.shutil.copy.assert_not_called()


def test_unknown_variant_with_no_requested_size(create_command, tmp_path, capsys):
    """If the app specifies an unknown variant, a message is reported."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source={
            "round": "input/original",
        },
        variant="unknown",
        size=None,
        target=out_path,
    )

    # The right message was written to output
    expected = "Unable to find unknown variant for sample image; using default\n"
    assert capsys.readouterr().out == expected

    # No file was installed.
    create_command.tools.shutil.copy.assert_not_called()


def test_variant_with_size(create_command, tmp_path, capsys):
    """If the app specifies a variant with a size, the sized variant is
    used."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original-3742.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source={
            "round": "input/original",
        },
        variant="round",
        size="3742",
        target=out_path,
    )

    # The right message was written to output
    expected = (
        "Installing input/original-3742.png as 3742px round sample image... done\n\n"
    )
    assert capsys.readouterr().out == expected

    # The file was copied into position
    create_command.tools.shutil.copy.assert_called_with(
        create_command.base_path / "input" / "original-3742.png",
        out_path,
    )


def test_variant_with_size_without_variants(create_command, tmp_path, capsys):
    """If the app specifies a variant with a size, but no variants are
    specified, a message is output."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original-3742.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source="input/original",
        variant="round",
        size="3742",
        target=out_path,
    )

    # The right message was written to output
    expected = "Unable to find 3742px round variant for sample image; using default\n"
    assert capsys.readouterr().out == expected

    # No file was installed.
    create_command.tools.shutil.copy.assert_not_called()


def test_unsized_variant(create_command, tmp_path, capsys):
    """If the app specifies an unsized variant, it is used."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    # Create the source image
    source_file = tmp_path / "project" / "input" / "original.png"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    with source_file.open("w") as f:
        f.write("image")

    # Try to install the image
    # Unsized variants are an annoying edge case; they get the *variant*
    # as the *size*.
    out_path = tmp_path / "output.png"
    create_command.install_image(
        "sample image",
        source={
            "round": "input/original",
        },
        variant=None,
        size="round",
        target=out_path,
    )

    # The right message was written to output
    expected = "Installing input/original.png as round sample image... done\n\n"
    assert capsys.readouterr().out == expected

    # The file was copied into position
    create_command.tools.shutil.copy.assert_called_with(
        create_command.base_path / "input" / "original.png",
        out_path,
    )
