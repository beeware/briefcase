from unittest.mock import MagicMock

import pytest

from briefcase.commands.new import LICENSE_OPTIONS

from ...utils import PartialMatchString


@pytest.mark.parametrize("license_file_name", ["LICENSE", "LICENCE"])
@pytest.mark.parametrize(
    "license_text, license_id",
    [
        ("MIT", "MIT"),
        ("MIT license", "MIT"),
        ("Permission is hereby granted, free of charge", "MIT"),
        ("Apache license", "Apache-2.0"),
        ("BSD", "BSD-3-Clause"),
        ("BSD license", "BSD-3-Clause"),
        # Includes some extra text to ensure it doesn't get caught as MIT because of
        # perMITted
        (
            "Redistribution and use in source and binary forms, with or without modification, are permitted",
            "BSD-3-Clause",
        ),
        ("GPLv2", "GPL-2.0"),
        ("version 2 of the GNU General Public License", "GPL-2.0"),
        ("GPLv2+", "GPL-2.0+"),
        ("Free Software Foundation, either version 2 of the License", "GPL-2.0+"),
        ("GPLv3", "GPL-3.0"),
        ("version 3 of the GNU General Public License", "GPL-3.0"),
        ("GPLv3+", "GPL-3.0+"),
        ("either version 3 of the License", "GPL-3.0+"),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_file(
    convert_command,
    license_text,
    license_id,
    license_file_name,
    monkeypatch,
):
    mock_selection_question = MagicMock()
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )

    dummy_license_text = (
        "some leading text\neven_more_text" + license_text + "some_ending_text\n"
    )
    (convert_command.base_path / license_file_name).write_text(
        dummy_license_text, encoding="utf-8"
    )

    convert_command.input_license(None)

    mock_selection_question.assert_called_once_with(
        intro=PartialMatchString("Based on the license file"),
        description="Project License",
        options=LICENSE_OPTIONS,
        default=license_id,
        override_value=None,
    )


@pytest.mark.parametrize(
    "license_text, license_id",
    [
        ("MIT", "MIT"),
        ("MIT license", "MIT"),
        ("Permission is hereby granted, free of charge", "MIT"),
        ("Apache license", "Apache-2.0"),
        ("BSD", "BSD-3-Clause"),
        ("BSD license", "BSD-3-Clause"),
        # Includes some extra text to ensure it doesn't get caught as MIT because of
        # perMITted
        (
            "Redistribution and use in source and binary forms, with or without modification, are permitted",
            "BSD-3-Clause",
        ),
        ("GPLv2", "GPL-2.0"),
        ("version 2 of the GNU General Public License", "GPL-2.0"),
        ("GPLv2+", "GPL-2.0+"),
        ("Free Software Foundation, either version 2 of the License", "GPL-2.0+"),
        ("GPLv3", "GPL-3.0"),
        ("version 3 of the GNU General Public License", "GPL-3.0"),
        ("GPLv3+", "GPL-3.0+"),
        ("either version 3 of the License", "GPL-3.0+"),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_pep621_license_file(
    convert_command,
    license_text,
    license_id,
    monkeypatch,
):
    mock_selection_question = MagicMock()
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )

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

    mock_selection_question.assert_called_once_with(
        intro=PartialMatchString("Based on the license file"),
        description="Project License",
        options=LICENSE_OPTIONS,
        default=license_id,
        override_value=None,
    )


@pytest.mark.parametrize(
    "license_text, license_id",
    [
        ("MIT", "MIT"),
        ("MIT license", "MIT"),
        ("BSD", "BSD-3-Clause"),
        ("BSD license", "BSD-3-Clause"),
        ("GPLv2", "GPL-2.0"),
        ("GPLv2+", "GPL-2.0+"),
        ("GPLv3", "GPL-3.0"),
        ("GPLv3+", "GPL-3.0+"),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_pyproject(
    convert_command,
    license_text,
    license_id,
    monkeypatch,
):
    mock_selection_question = MagicMock()
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n" f'license = {{text = "{license_text}"}}', encoding="utf-8"
    )

    convert_command.input_license(None)

    mock_selection_question.assert_called_once_with(
        intro=PartialMatchString("Based on the PEP621 formatted pyproject.toml"),
        description="Project License",
        options=LICENSE_OPTIONS,
        default=license_id,
        override_value=None,
    )


def test_no_license_hint(convert_command, monkeypatch):
    mock_selection_question = MagicMock()
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )

    convert_command.input_license(None)

    assert mock_selection_question.call_count == 1
    assert mock_selection_question.call_args.kwargs["default"] is None
    assert "Based on" not in mock_selection_question.call_args.kwargs["intro"]


def test_override_is_used(convert_command):
    assert convert_command.input_license("Proprietary") == "Proprietary"
