from unittest.mock import MagicMock

import pytest

from ...utils import PartialMatchString


@pytest.mark.parametrize("license_file_name", ["LICENSE", "LICENCE"])
@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT License (MIT)"),
        ("MIT License (MIT)", "MIT License (MIT)"),
        ("Permission is hereby granted, free of charge", "MIT License (MIT)"),
        ("Apache license", "Apache License 2.0 (Apache-2.0)"),
        ("BSD", 'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)'),
        (
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
        ),
        # Includes some extra text to ensure it doesn't get caught as MIT because of
        # perMITted
        (
            "Redistribution and use in source and binary forms, with or without modification, are permitted",
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
        ),
        ("GPLv2", "GNU General Public License v2.0 only (GPL-2.0)"),
        (
            "version 2 of the GNU General Public License",
            "GNU General Public License v2.0 only (GPL-2.0)",
        ),
        ("GPLv2+", "GNU General Public License v2.0 or later (GPL-2.0+)"),
        (
            "Free Software Foundation, either version 2 of the License",
            "GNU General Public License v2.0 or later (GPL-2.0+)",
        ),
        ("GPLv3", "GNU General Public License v3.0 only (GPL-3.0)"),
        (
            "version 3 of the GNU General Public License",
            "GNU General Public License v3.0 only (GPL-3.0)",
        ),
        ("GPLv3+", "GNU General Public License v3.0 or later (GPL-3.0+)"),
        (
            "either version 3 of the License",
            "GNU General Public License v3.0 or later (GPL-3.0+)",
        ),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_file(
    convert_command, license_text, license, license_file_name, monkeypatch
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
        intro=PartialMatchString("the license file"),
        description="Project License",
        options=[
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            "MIT License (MIT)",
            "Apache License 2.0 (Apache-2.0)",
            "GNU General Public License v2.0 only (GPL-2.0)",
            "GNU General Public License v2.0 or later (GPL-2.0+)",
            "GNU General Public License v3.0 only (GPL-3.0)",
            "GNU General Public License v3.0 or later (GPL-3.0+)",
            "Proprietary",
            "Other",
        ],
        default=license,
        override_value=None,
    )


@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT License (MIT)"),
        ("MIT License (MIT)", "MIT License (MIT)"),
        ("Permission is hereby granted, free of charge", "MIT License (MIT)"),
        ("Apache license", "Apache License 2.0 (Apache-2.0)"),
        ("BSD", 'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)'),
        (
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
        ),
        # Includes some extra text to ensure it doesn't get caught as MIT because of
        # perMITted
        (
            "Redistribution and use in source and binary forms, with or without modification, are permitted",
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
        ),
        ("GPLv2", "GNU General Public License v2.0 only (GPL-2.0)"),
        (
            "version 2 of the GNU General Public License",
            "GNU General Public License v2.0 only (GPL-2.0)",
        ),
        ("GPLv2+", "GNU General Public License v2.0 or later (GPL-2.0+)"),
        (
            "Free Software Foundation, either version 2 of the License",
            "GNU General Public License v2.0 or later (GPL-2.0+)",
        ),
        ("GPLv3", "GNU General Public License v3.0 only (GPL-3.0)"),
        (
            "version 3 of the GNU General Public License",
            "GNU General Public License v3.0 only (GPL-3.0)",
        ),
        ("GPLv3+", "GNU General Public License v3.0 or later (GPL-3.0+)"),
        (
            "either version 3 of the License",
            "GNU General Public License v3.0 or later (GPL-3.0+)",
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
        intro=PartialMatchString("the license file"),
        description="Project License",
        options=[
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            "MIT License (MIT)",
            "Apache License 2.0 (Apache-2.0)",
            "GNU General Public License v2.0 only (GPL-2.0)",
            "GNU General Public License v2.0 or later (GPL-2.0+)",
            "GNU General Public License v3.0 only (GPL-3.0)",
            "GNU General Public License v3.0 or later (GPL-3.0+)",
            "Proprietary",
            "Other",
        ],
        default=license,
        override_value=None,
    )


@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT License (MIT)"),
        ("MIT License (MIT)", "MIT License (MIT)"),
        ("BSD", 'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)'),
        (
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
        ),
        ("GPLv2", "GNU General Public License v2.0 only (GPL-2.0)"),
        ("GPLv2+", "GNU General Public License v2.0 or later (GPL-2.0+)"),
        ("GPLv3", "GNU General Public License v3.0 only (GPL-3.0)"),
        ("GPLv3+", "GNU General Public License v3.0 or later (GPL-3.0+)"),
        ("Some text", "Other"),
    ],
)
def test_get_license_from_pyproject(
    convert_command,
    license_text,
    license,
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
        intro=PartialMatchString("the PEP621 formatted pyproject.toml"),
        description="Project License",
        options=[
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            "MIT License (MIT)",
            "Apache License 2.0 (Apache-2.0)",
            "GNU General Public License v2.0 only (GPL-2.0)",
            "GNU General Public License v2.0 or later (GPL-2.0+)",
            "GNU General Public License v3.0 only (GPL-3.0)",
            "GNU General Public License v3.0 or later (GPL-3.0+)",
            "Proprietary",
            "Other",
        ],
        default=license,
        override_value=None,
    )


def test_no_license_hint(convert_command, monkeypatch):
    mock_selection_question = MagicMock()
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )

    convert_command.input_license(None)
    mock_selection_question.assert_called_once_with(
        intro="What license do you want to use for this project's code? ",
        description="Project License",
        options=[
            'BSD 3-Clause "New" or "Revised" License (BSD-3-Clause)',
            "MIT License (MIT)",
            "Apache License 2.0 (Apache-2.0)",
            "GNU General Public License v2.0 only (GPL-2.0)",
            "GNU General Public License v2.0 or later (GPL-2.0+)",
            "GNU General Public License v3.0 only (GPL-3.0)",
            "GNU General Public License v3.0 or later (GPL-3.0+)",
            "Proprietary",
            "Other",
        ],
        default=None,
        override_value=None,
    )


def test_override_is_used(convert_command):
    assert convert_command.input_license("Proprietary") == "Proprietary"
