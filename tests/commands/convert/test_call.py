from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "cmdline, overrides",
    [
        ([], {}),
        (["-Q", "license=MIT"], {"license": "MIT"}),
        (
            ["-Q", "license=MIT", "-Q", "bootstrap=Toga"],
            {"license": "MIT", "bootstrap": "Toga"},
        ),
    ],
)
def test_convert_app(convert_command, cmdline, overrides, patch_tempdir):
    """An application can be set up for briefcase created."""
    (convert_command.base_path / "app_name").mkdir()
    (convert_command.base_path / "pyproject.toml").write_text("", encoding="utf-8")
    (convert_command.base_path / "app_name/__main__.py").write_text(
        "", encoding="utf-8"
    )

    # Configure no command line options
    options, _ = convert_command.parse_options(cmdline)

    # Run the run command
    convert_command(**options)

    # The right sequence of things will be done
    assert convert_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # Pyproject doesn't contain Briefcase config
        ("validate-pyproject-file",),
        # Run the first app
        (
            "new",
            {
                "template": None,
                "template_branch": None,
                "project_overrides": overrides,
                "tmp_path": Path(patch_tempdir.name),
            },
        ),
    ]
