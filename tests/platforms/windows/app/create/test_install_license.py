from textwrap import dedent

import pytest

from briefcase.exceptions import BriefcaseCommandError

from .....utils import create_file


def test_license_file_txt(create_command, first_app_templated, tmp_path):
    """A license can be specified as a TXT file."""
    create_file(tmp_path / "base_path/LICENSE", "This is a license file")

    create_command.install_license(first_app_templated)

    # A LICENSE.rtf file has been written, in RTF format, containing the license text.
    license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    assert license.is_file()

    license_text = license.read_text(encoding="utf-8")
    assert license_text.startswith("{\\rtf1\\ansi")
    assert "This is a license file" in license_text
    assert license_text.endswith("\n}")


def test_license_file_rtf(create_command, first_app_templated, tmp_path):
    """A license can be specified as an RTF file."""
    first_app_templated.license["file"] = "LICENSE.rtf"
    orig_license = tmp_path / "base_path/LICENSE.rtf"
    create_file(
        orig_license,
        dedent(
            """\
            {\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}
            This is a document that contains bullet points:\x20
            \\par\\line
            \\bullet first, something short\x20
            \\bullet then, something longer that needs to\x20
            run onto multiple lines\x20
            \\bullet last, something short again\x20
            \\par\\line
            Then a closing paragraph.\x20
            \\par\\line
            }"""
        ),
    )
    create_command.install_license(first_app_templated)

    # The license RTF file is the same as the original
    license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    assert license.is_file()
    assert license.read_text(encoding="utf-8") == orig_license.read_text(
        encoding="utf-8"
    )


def test_missing_license_file(create_command, first_app_templated):
    """If a named license file is missing, an error is raised."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"However, this file does not exist.",
    ):
        create_command.install_license(first_app_templated)


def test_license_text(create_command, first_app_templated, tmp_path):
    """A license provided as text is converted into a file."""
    del first_app_templated.license["file"]
    first_app_templated.license["text"] = "This is a license\nDo what you want."

    create_command.install_license(first_app_templated)

    # A license file was written, and contains the licence text
    license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    license_text = license.read_text(encoding="utf-8")
    assert license_text.startswith("{\\rtf1\\ansi")
    assert "This is a license " in license_text
    assert license_text.endswith("\n}")


def test_license_text_suspicious(create_command, first_app_templated, tmp_path, capsys):
    """A single line license text is flagged as suspicious, but converted."""
    del first_app_templated.license["file"]
    first_app_templated.license["text"] = "BSD 3 clause"

    create_command.install_license(first_app_templated)

    license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    assert license.is_file()

    license_text = license.read_text(encoding="utf-8")
    assert license_text.startswith("{\\rtf1\\ansi")
    assert "BSD 3 clause" in license_text
    assert license_text.endswith("\n}")

    # The user was warned that the text probably isn't a full license
    console = capsys.readouterr().out
    assert "ensure that the contents of this file is adequate." in console


def test_no_license(create_command, first_app_templated):
    """If an app doesn't provide a known license definition, an error is raised."""
    del first_app_templated.license["file"]
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Your project does not contain a `license` definition.",
    ):
        create_command.install_license(first_app_templated)
