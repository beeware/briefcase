import pytest

from briefcase.exceptions import BriefcaseConfigError

from .....utils import create_file


def test_license_file_txt(create_command, first_app_templated, tmp_path):
    """A plain-text license file is converted to RTF."""
    create_file(tmp_path / "base_path/LICENSE", "This is a license file")
    first_app_templated.license = "MIT"
    first_app_templated.license_files = ["LICENSE"]

    create_command.install_license(first_app_templated)

    # A LICENSE.rtf file has been written, in RTF format, containing the license text.
    license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    assert license.is_file()

    license_text = license.read_text(encoding="utf-8")
    assert license_text.startswith("{\\rtf1\\ansi")
    assert "This is a license file" in license_text
    assert license_text.endswith("\n}")


def test_license_file_rtf(create_command, first_app_templated, tmp_path):
    """A native RTF license file is copied directly."""
    orig_rtf = (
        "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}\n"
        "This is a document that contains bullet points: \n"
        "\\par\\line\n"
        "\\bullet first, something short \n"
        "\\par\\line\n"
        "Then a closing paragraph. \n"
        "\\par\\line\n"
        "}"
    )
    orig_license = tmp_path / "base_path/LICENSE.rtf"
    create_file(orig_license, orig_rtf)
    first_app_templated.license = "MIT"
    first_app_templated.license_files = ["LICENSE.rtf"]

    create_command.install_license(first_app_templated)

    # The output LICENSE.rtf should be an identical copy of the original.
    dest_license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    assert dest_license.is_file()
    result = dest_license.read_text(encoding="utf-8")
    assert result == orig_rtf


def test_license_file_multi(create_command, first_app_templated, tmp_path):
    """Multiple plain-text license files are merged with an RTF separator."""
    create_file(tmp_path / "base_path/LICENSE-A", "Apache License text")
    create_file(tmp_path / "base_path/LICENSE-B", "MIT License text")
    first_app_templated.license = "Apache-2.0 AND MIT"
    first_app_templated.license_files = ["LICENSE-A", "LICENSE-B"]

    create_command.install_license(first_app_templated)

    license = tmp_path / "base_path/build/first-app/windows/app/LICENSE.rtf"
    assert license.is_file()
    result = license.read_text(encoding="utf-8")
    assert result.startswith("{\\rtf1\\ansi")
    assert "Apache License text" in result
    assert "MIT License text" in result
    assert "\\brdrb\\brdrs" in result  # RTF separator was inserted
    assert result.endswith("\n}")


def test_license_file_multi_with_rtf_raises(
    create_command,
    first_app_templated,
    tmp_path,
):
    """When multiple license files include an RTF file, a BriefcaseConfigError is
    raised."""
    create_file(
        tmp_path / "base_path/LICENSE-A.rtf",
        "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}Apache License text.\\par\\line}",
    )
    create_file(tmp_path / "base_path/LICENSE-B", "MIT License text")
    first_app_templated.license = "Apache-2.0 AND MIT"
    first_app_templated.license_files = ["LICENSE-A.rtf", "LICENSE-B"]

    with pytest.raises(
        BriefcaseConfigError,
        match=r"contains multiple\nlicense files, and at least one is an RTF file",
    ):
        create_command.install_license(first_app_templated)


def test_license_file_multi_all_rtf_raises(
    create_command,
    first_app_templated,
    tmp_path,
):
    """When multiple RTF files are provided, a BriefcaseConfigError is raised."""
    rtf = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}Some text.\\par\\line}"
    create_file(tmp_path / "base_path/LICENSE-A.rtf", rtf)
    create_file(tmp_path / "base_path/LICENSE-B.rtf", rtf)
    first_app_templated.license = "Apache-2.0 AND MIT"
    first_app_templated.license_files = ["LICENSE-A.rtf", "LICENSE-B.rtf"]

    with pytest.raises(
        BriefcaseConfigError,
        match=r"contains multiple\nlicense files, and at least one is an RTF file",
    ):
        create_command.install_license(first_app_templated)
