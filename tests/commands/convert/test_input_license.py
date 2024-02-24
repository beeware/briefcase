from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT license"),
        ("MIT license", "MIT license"),
        ("Permission is hereby granted, free of charge", "MIT license"),
        ("Apache license", "Apache Software License"),
        ("BSD", "BSD license"),
        ("BSD license", "BSD license"),
        ("Redistribution and use in source and binary forms", "BSD license"),
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
def test_get_license_from_file(convert_command, license_text, license, monkeypatch):
    m_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", m_select_option)

    (convert_command.base_path / "LICENSE").write_text(license_text, encoding="utf-8")

    convert_command.input_license(None)
    m_select_option.assert_called_once()
    assert m_select_option.call_args.kwargs["default"] == license
    assert "the license file" in m_select_option.call_args.kwargs["intro"]
    assert license in m_select_option.call_args.kwargs["options"]


@pytest.mark.parametrize(
    "license_text, license",
    [
        ("MIT", "MIT license"),
        ("MIT license", "MIT license"),
        ("Permission is hereby granted, free of charge", "MIT license"),
        ("Apache license", "Apache Software License"),
        ("BSD", "BSD license"),
        ("BSD license", "BSD license"),
        ("Redistribution and use in source and binary forms", "BSD license"),
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
    convert_command, license_text, license, monkeypatch
):
    m_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", m_select_option)
    (convert_command.base_path / "LICENSE.txt").write_text(
        license_text, encoding="utf-8"
    )
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n" 'license = {file = "LICENSE.txt"}', encoding="utf-8"
    )

    convert_command.input_license(None)
    m_select_option.assert_called_once()
    assert m_select_option.call_args.kwargs["default"] == license
    assert "the license file" in m_select_option.call_args.kwargs["intro"]
    assert license in m_select_option.call_args.kwargs["options"]


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
    convert_command, license_text, license, monkeypatch
):
    m_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", m_select_option)
    (convert_command.base_path / "pyproject.toml").write_text(
        "[project]\n" f'license = {{text = "{license_text}"}}', encoding="utf-8"
    )

    convert_command.input_license(None)
    m_select_option.assert_called_once()
    assert m_select_option.call_args.kwargs["default"] == license
    assert (
        "the PEP621 formatted pyproject.toml"
        in m_select_option.call_args.kwargs["intro"]
    )
    assert license in m_select_option.call_args.kwargs["options"]


def test_no_license_hint(convert_command, monkeypatch):
    m_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", m_select_option)

    convert_command.input_license(None)
    m_select_option.assert_called_once()
    assert m_select_option.call_args.kwargs["default"] is None
    assert "the license file" not in m_select_option.call_args.kwargs["intro"]
    assert (
        "the PEP621 formatted pyproject.toml"
        not in m_select_option.call_args.kwargs["intro"]
    )
