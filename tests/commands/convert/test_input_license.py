from unittest.mock import MagicMock

import pytest

from ...utils import PartialMatchString


@pytest.mark.parametrize("license_file_name", ["LICENSE", "LICENCE"])
@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT license"),
        ("MIT license", "MIT license"),
        ("Permission is hereby granted, free of charge", "MIT license"),
        ("Apache license", "Apache Software License"),
        ("BSD", "BSD license"),
        ("BSD license", "BSD license"),
        # Includes some extra text to ensure it doesn't get caught as MIT because of
        # perMITted
        (
            "Redistribution and use in source and binary forms, with or without modification, are permitted",
            "BSD license",
        ),
        ("GPLv2", "GNU General Public License v2 (GPLv2)"),
        (
            "version 2 of the GNU General Public License",
            "GNU General Public License v2 (GPLv2)",
        ),
        ("GPLv2+", "GNU General Public License v2 or later (GPLv2+)"),
        (
            "Free Software Foundation, either version 2 of the License",
            "GNU General Public License v2 or later (GPLv2+)",
        ),
        ("GPLv3", "GNU General Public License v3 (GPLv3)"),
        (
            "version 3 of the GNU General Public License",
            "GNU General Public License v3 (GPLv3)",
        ),
        ("GPLv3+", "GNU General Public License v3 or later (GPLv3+)"),
        (
            "either version 3 of the License",
            "GNU General Public License v3 or later (GPLv3+)",
        ),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_file(
    convert_command, license_text, license, license_file_name, monkeypatch
):
    mock_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    dummy_license_text = (
        "some leading text\neven_more_text" + license_text + "some_ending_text\n"
    )
    (convert_command.base_path / license_file_name).write_text(
        dummy_license_text, encoding="utf-8"
    )

    convert_command.input_license(None)
    mock_select_option.assert_called_once_with(
        intro=PartialMatchString("the license file"),
        variable="Project License",
        options=[
            "BSD license",
            "MIT license",
            "Apache Software License",
            "GNU General Public License v2 (GPLv2)",
            "GNU General Public License v2 or later (GPLv2+)",
            "GNU General Public License v3 (GPLv3)",
            "GNU General Public License v3 or later (GPLv3+)",
            "Proprietary",
            "Other",
        ],
        default=license,
        override_value=None,
    )


@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT license"),
        ("MIT license", "MIT license"),
        ("Permission is hereby granted, free of charge", "MIT license"),
        ("Apache license", "Apache Software License"),
        ("BSD", "BSD license"),
        ("BSD license", "BSD license"),
        # Includes some extra text to ensure it doesn't get caught as MIT because of
        # perMITted
        (
            "Redistribution and use in source and binary forms, with or without modification, are permitted",
            "BSD license",
        ),
        ("GPLv2", "GNU General Public License v2 (GPLv2)"),
        (
            "version 2 of the GNU General Public License",
            "GNU General Public License v2 (GPLv2)",
        ),
        ("GPLv2+", "GNU General Public License v2 or later (GPLv2+)"),
        (
            "Free Software Foundation, either version 2 of the License",
            "GNU General Public License v2 or later (GPLv2+)",
        ),
        ("GPLv3", "GNU General Public License v3 (GPLv3)"),
        (
            "version 3 of the GNU General Public License",
            "GNU General Public License v3 (GPLv3)",
        ),
        ("GPLv3+", "GNU General Public License v3 or later (GPLv3+)"),
        (
            "either version 3 of the License",
            "GNU General Public License v3 or later (GPLv3+)",
        ),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_pep621_license_file(
    convert_command,
    license_text,
    license,
    monkeypatch,
):
    mock_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    dummy_license_text = (
        "some leading text\neven_more_text" + license_text + "some_ending_text\n"
    )
    (convert_command.base_path / "LICENSE.txt").write_text(
        dummy_license_text, encoding="utf-8"
    )
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n" 'license = {file = "LICENSE.txt"}', encoding="utf-8"
    )

    convert_command.input_license(None)

    mock_select_option.assert_called_once_with(
        intro=PartialMatchString("the license file"),
        variable="Project License",
        options=[
            "BSD license",
            "MIT license",
            "Apache Software License",
            "GNU General Public License v2 (GPLv2)",
            "GNU General Public License v2 or later (GPLv2+)",
            "GNU General Public License v3 (GPLv3)",
            "GNU General Public License v3 or later (GPLv3+)",
            "Proprietary",
            "Other",
        ],
        default=license,
        override_value=None,
    )


@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT license"),
        ("MIT license", "MIT license"),
        ("BSD", "BSD license"),
        ("BSD license", "BSD license"),
        ("GPLv2", "GNU General Public License v2 (GPLv2)"),
        ("GPLv2+", "GNU General Public License v2 or later (GPLv2+)"),
        ("GPLv3", "GNU General Public License v3 (GPLv3)"),
        ("GPLv3+", "GNU General Public License v3 or later (GPLv3+)"),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_pyproject(
    convert_command,
    license_text,
    license,
    monkeypatch,
):
    mock_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n" f'license = {{text = "{license_text}"}}', encoding="utf-8"
    )

    convert_command.input_license(None)
    mock_select_option.assert_called_once_with(
        intro=PartialMatchString("the PEP621 formatted pyproject.toml"),
        variable="Project License",
        options=[
            "BSD license",
            "MIT license",
            "Apache Software License",
            "GNU General Public License v2 (GPLv2)",
            "GNU General Public License v2 or later (GPLv2+)",
            "GNU General Public License v3 (GPLv3)",
            "GNU General Public License v3 or later (GPLv3+)",
            "Proprietary",
            "Other",
        ],
        default=license,
        override_value=None,
    )


def test_no_license_hint(convert_command, monkeypatch):
    mock_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    convert_command.input_license(None)
    mock_select_option.assert_called_once_with(
        intro="What license do you want to use for this project's code? ",
        variable="Project License",
        options=[
            "BSD license",
            "MIT license",
            "Apache Software License",
            "GNU General Public License v2 (GPLv2)",
            "GNU General Public License v2 or later (GPLv2+)",
            "GNU General Public License v3 (GPLv3)",
            "GNU General Public License v3 or later (GPLv3+)",
            "Proprietary",
            "Other",
        ],
        default=None,
        override_value=None,
    )


def test_override_is_used(convert_command):
    assert convert_command.input_license("Proprietary") == "Proprietary"
