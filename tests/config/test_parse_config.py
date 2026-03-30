import subprocess
from email.message import Message
from unittest.mock import Mock

import pytest
from build import BuildBackendException

from briefcase.config import parse_config
from briefcase.console import Console
from briefcase.exceptions import BriefcaseConfigError
from tests.utils import create_file


def test_invalid_toml(tmp_path):
    """If the config file isn't TOML, raise an error."""
    config_file = create_file(tmp_path / "pyproject.toml", "this is not toml!")

    with pytest.raises(BriefcaseConfigError, match=r"Invalid pyproject\.toml"):
        parse_config(
            config_file,
            platform="macOS",
            output_format="Xcode",
            console=Mock(),
        )


def test_no_briefcase_section(tmp_path):
    """If the config file doesn't contain a briefcase tool section, raise an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.section]
        name="value"
        number=42
        """,
    )

    with pytest.raises(BriefcaseConfigError, match=r"No tool\.briefcase section"):
        parse_config(
            config_file,
            platform="macOS",
            output_format="Xcode",
            console=Mock(),
        )


def test_no_apps(tmp_path):
    """If the config file doesn't contain at least one briefcase app, raise an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        name="value"
        number=42
        """,
    )

    with pytest.raises(BriefcaseConfigError, match="No Briefcase apps defined"):
        parse_config(
            config_file,
            platform="macOS",
            output_format="Xcode",
            console=Mock(),
        )


def test_single_minimal_app(tmp_path):
    """A single app can be defined, but can exist without any app attributes."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT"
        value = 42

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="Xcode",
        console=console,
    )

    # There's a single global option, plus a license and empty license files.
    assert global_options == {
        "value": 42,
        "license": "MIT",
    }

    # The app gets the name from its header line.
    # It inherits the value from the base definition.
    # It gets a guess at a license
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "value": 42,
            "license": "MIT",
            "license_files": [],
        }
    }

    # No warnings
    console.warning.assert_not_called()


def test_multiple_minimal_apps(tmp_path):
    """The configuration can contain multiple apps without an explicit tool header."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase.app.first]
        number=37
        license="MIT"

        [tool.briefcase.app.second]
        number=42
        license="BSD-3-Clause"
        """,
    )

    console = Mock()
    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="Xcode",
        console=console,
    )

    # There are no global options
    assert global_options == {}

    # The apps get their name from the header lines.
    # The second tool overrides its app name
    assert apps == {
        "first": {
            "app_name": "first",
            "number": 37,
            "license": "MIT",
            "license_files": [],
        },
        "second": {
            "app_name": "second",
            "number": 42,
            "license": "BSD-3-Clause",
            "license_files": [],
        },
    }

    # No warnings
    console.warning.assert_not_called()


def test_platform_override(tmp_path):
    """An app can define platform settings that override base settings."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        basevalue = "the base"
        license = "MIT"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"
        license = "BSD-3-Clause"

        [tool.briefcase.app.my_app.macOS]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.linux]
        value = 3
        platformvalue = "linux platform"

        [tool.briefcase.app.other_app.macOS]
        value = 4
        platformvalue = "other macos platform"
        """,
    )

    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="Xcode",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "basevalue": "the base",
        "license": "MIT",
    }

    # Since a macOS app has been requested, the macOS platform values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Platforms should be processed in sorted order, which means that linux
    # will be processed before macOS.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "value": 2,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
            "license": "BSD-3-Clause",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
            "license": "MIT",
            "license_files": [],
        },
    }


def test_platform_override_ordering(tmp_path):
    """The order of platform processing doesn't affect output."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        basevalue = "the base"
        license = "MIT"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macOS]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.windows]
        value = 3
        platformvalue = "windows platform"

        [tool.briefcase.app.other_app.macOS]
        value = 4
        platformvalue = "other macos platform"
        """,
    )

    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="Xcode",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "basevalue": "the base",
        "license": "MIT",
    }

    # Since a macOS app has been requested, the macOS platform values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Platforms should be processed in order, which means that windows
    # will be processed after macOS.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "value": 2,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
            "license": "MIT",
            "license_files": [],
        },
    }


def test_format_override(tmp_path):
    """An app can define format settings that override base and platform settings."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT"
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macOS]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.macOS.app]
        value = 21
        formatvalue = "app format"

        [tool.briefcase.app.my_app.macOS.Xcode]
        value = 22
        formatvalue = "xcode format"

        [tool.briefcase.app.my_app.linux]
        value = 3
        platformvalue = "linux platform"

        [tool.briefcase.app.my_app.linux.snap]
        value = 31
        formatvalue = "snap format"

        [tool.briefcase.app.my_app.linux.appimage]
        value = 32
        formatvalue = "appimage format"

        [tool.briefcase.app.other_app.macOS.app]
        value = 41
        formatvalue = "other macos app format"
        """,
    )

    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "basevalue": "the base",
        "license": "MIT",
    }

    # Since a macOS app has been requested, the macOS app format values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Formats should be processed in order, which means that app
    # will be processed before dmg.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "value": 21,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
            "formatvalue": "app format",
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 41,
            "basevalue": "the base",
            "formatvalue": "other macos app format",
            "license": "MIT",
            "license_files": [],
        },
    }


def test_format_override_ordering(tmp_path):
    """The order of format processing doesn't affect output."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT"
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macOS]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.macOS.Xcode]
        value = 21
        formatvalue = "app format"

        [tool.briefcase.app.my_app.macOS.app]
        value = 22
        formatvalue = "app format"

        [tool.briefcase.app.my_app.linux]
        value = 3
        platformvalue = "linux platform"

        [tool.briefcase.app.my_app.linux.snap]
        value = 31
        formatvalue = "snap format"

        [tool.briefcase.app.my_app.linux.appimage]
        value = 32
        formatvalue = "appimage format"

        [tool.briefcase.app.other_app.macOS.Xcode]
        value = 41
        formatvalue = "other macos app format"
        """,
    )

    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "basevalue": "the base",
        "license": "MIT",
    }

    # Since a macOS dmg has been requested, the macOS dmg format values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Formats should be processed in order, which means that dmg
    # will be processed after app.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "value": 22,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
            "formatvalue": "app format",
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 0,
            "basevalue": "the base",
            "license": "MIT",
            "license_files": [],
        },
    }


def test_requires(tmp_path):
    """Requirements can be specified."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license = "MIT"
        requires = ["base value"]

        [tool.briefcase.app.my_app]
        requires = ["my_app value"]

        [tool.briefcase.app.my_app.macOS]
        requires = ["macos value"]

        [tool.briefcase.app.my_app.macOS.Xcode]
        requires = ["xcode value"]

        [tool.briefcase.app.my_app.macOS.app]
        requires = ["app value"]

        [tool.briefcase.app.my_app.linux]
        requires = ["linux value"]

        [tool.briefcase.app.my_app.linux.appimage]
        requires = ["appimage value"]

        [tool.briefcase.app.other_app]
        """,
    )

    # Request a macOS app
    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "requires": ["base value"],
        "license": "MIT",
    }

    # The macOS my_app app specifies a full inherited chain.
    # The other_app app doesn't specify any options.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "requires": [
                "base value",
                "my_app value",
                "macos value",
                "app value",
            ],
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
    }

    # Request a macOS xcode project
    global_options, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="Xcode",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "requires": ["base value"],
        "license": "MIT",
    }

    # The macOS my_app dmg specifies a full inherited chain.
    # The other_app dmg doesn't specify any options.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "requires": [
                "base value",
                "my_app value",
                "macos value",
                "xcode value",
            ],
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
    }

    global_options, apps = parse_config(
        config_file,
        platform="linux",
        output_format="appimage",
        console=Mock(),
    )

    # The global options are exactly as specified
    assert global_options == {
        "value": 0,
        "requires": ["base value"],
        "license": "MIT",
    }

    # The linux my_app appimage overrides the *base* value, but extends for linux.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "requires": [
                "base value",
                "my_app value",
                "linux value",
                "appimage value",
            ],
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
    }


def test_document_types(tmp_path):
    """Document types can be specified."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license = "MIT"

        [tool.briefcase.app.my_app]

        [tool.briefcase.app.my_app.macOS]

        [tool.briefcase.app.my_app.macOS.document_type.document]
        extension = "doc"
        description = "A document"

        [tool.briefcase.app.my_app.macOS.document_type.image]
        extension = "img"
        description = "An image"

        [tool.briefcase.app.other_app]

        """,
    )

    # Request a macOS app
    _, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="Xcode",
        console=Mock(),
    )

    # The macOS my_app app specifies a full inherited chain.
    # The other_app app doesn't specify any options.
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "document_type": {
                "document": {
                    "extension": "doc",
                    "description": "A document",
                },
                "image": {
                    "extension": "img",
                    "description": "An image",
                },
            },
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 0,
            "license": "MIT",
            "license_files": [],
        },
    }


def test_pep_621_merge(tmp_path):
    """PEP 621 [project] fields are merged into the Briefcase config."""
    # A license file must exist. The definition is split across `project` and
    # `tool.briefcase` to prove merging happens
    (tmp_path / "LICENSE").write_text("MIT License text", encoding="utf-8")

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "awesome"
        version = "1.2.3"
        authors = [{name = "Kim Park", email = "kim@example.com"}]
        dependencies = ["numpy"]
        description = "awesome project"
        license-files = ["LICENSE"]

        [project.urls]
        Homepage = "https://example.com/awesome"

        [project.optional-dependencies]
        test = ["pytest"]

        [tool.briefcase]
        project_name = "Awesome app"
        bundle = "com.example"
        license = "MIT"

        [tool.briefcase.app.awesome]
        formal_name = "Awesome Application"
        long_description = "The application is very awesome"
        sources = [
            "src",
        ]
        test_sources = [
            "tests",
        ]

        [tool.briefcase.app.awesome.macOS]
        requires = [
            "toga-cocoa~=0.3.1",
            "std-nslog~=1.0.3"
        ]
        """,
    )

    _, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=Mock(),
    )

    awesome = apps["awesome"]
    assert awesome == {
        "project_name": "Awesome app",
        "bundle": "com.example",
        "version": "1.2.3",
        "license": "MIT",
        "license_files": ["LICENSE"],
        "author": "Kim Park",
        "author_email": "kim@example.com",
        "url": "https://example.com/awesome",
        "description": "awesome project",
        "requires": ["numpy", "toga-cocoa~=0.3.1", "std-nslog~=1.0.3"],
        "test_requires": ["pytest"],
        "app_name": "awesome",
        "sources": ["src"],
        "test_sources": ["tests"],
        "formal_name": "Awesome Application",
        "long_description": "The application is very awesome",
    }


def test_license_pep621_table_with_files_is_error(tmp_path):
    """PEP 621 table format mixed with license-files raises an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license-files = ["LICENSE"]

        [tool.briefcase.license]
        file = "LICENSE"

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"mixes PEP 621 table",
    ):
        parse_config(
            config_file,
            platform="macOS",
            output_format="app",
            console=Mock(),
        )


def test_license_files_without_license_is_error(tmp_path):
    """Specifying license-files without a license expression raises an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license-files = ["LICENSE"]

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"defines `license-files` but no\n`license` SPDX expression.",
    ):
        parse_config(
            config_file,
            platform="macOS",
            output_format="app",
            console=Mock(),
        )


def test_license_pep639_empty_list(tmp_path):
    """An empty license files list is valid."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT"
        license-files = []

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license_files"] == []
    console.warning.assert_not_called()


def test_license_pep639_invalid_spdx_with_files(tmp_path):
    """Non-SPDX license string with license-files raises an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "BSD License"
        license-files = ["LICENSE"]

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"is not a valid SPDX expression",
    ):
        parse_config(
            config_file,
            platform="macOS",
            output_format="app",
            console=Mock(),
        )


@pytest.mark.parametrize(
    "config",
    [
        # license in a project block
        """
        [project]
        license = "MIT"

        [tool.briefcase.app.my_app]
        """,
        # license in a tool.briefcase block
        """
        [tool.briefcase]
        license = "MIT"

        [tool.briefcase.app.my_app]
        """,
    ],
)
def test_license_pep639_spdx_without_files(config, tmp_path):
    """PEP 639 license, with *no* license files defined."""
    config_path = create_file(tmp_path / "pyproject.toml", config)

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license_files"] == []
    console.warning.assert_not_called()


def test_license_pep639_missing_file(tmp_path):
    """A PEP 639 config where a license file is missing raises an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT"
        license-files = ["LICENSE"]

        [tool.briefcase.app.my_app]
        """,
    )
    # Do NOT create the LICENSE file.

    with pytest.raises(
        BriefcaseConfigError,
        match=r"The license file 'LICENSE' for 'my_app' does not exist",
    ):
        parse_config(
            config_file,
            platform="macOS",
            output_format="app",
            console=Mock(),
        )


def test_license_pep639_valid(tmp_path):
    """A valid PEP 639 license config (complex SDPX + multiple files) is accepted."""
    (tmp_path / "LICENSE").write_text("MIT License text", encoding="utf-8")
    (tmp_path / "LICENSE-other").write_text("BSD License text", encoding="utf-8")

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT AND BSD-3-Clause"
        license-files = ["LICENSE", "LICENSE-other"]

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "MIT AND BSD-3-Clause"
    assert apps["my_app"]["license_files"] == ["LICENSE", "LICENSE-other"]
    console.warning.assert_not_called()


def test_license_pep639_normalized(tmp_path):
    """SPDX expressions are normalized to canonical case."""
    (tmp_path / "LICENSE").write_text("MIT License text", encoding="utf-8")

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "mit"
        license-files = ["LICENSE"]

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license_files"] == ["LICENSE"]
    console.warning.assert_not_called()


@pytest.mark.parametrize(
    "config",
    [
        # license in a project block
        """
        [project]
        license.text = "MIT License text"

        [tool.briefcase.app.my_app]
        sources = ["src"]
        """,
        # license in a tool.briefcase block
        """
        [tool.briefcase]
        license.text = "MIT License text"

        [tool.briefcase.app.my_app]
        sources = ["src"]
        """,
    ],
)
def test_license_pep621_text_spdx(config, tmp_path):
    """PEP 621 license.text: recognizable SPDX text is coerced."""
    config_path = create_file(tmp_path / "pyproject.toml", config)

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license_files"] == []

    # The license text was not written
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert not license_text_file.exists()

    # One warning hinting an identified license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.text` format" in warning_text
    assert "may not be correct, and should be verified." not in warning_text
    assert "LicenseRef-UnknownLicense" not in warning_text
    assert 'license = "MIT"' in warning_text


def test_license_pep621_text_non_spdx(tmp_path):
    """PEP 621 license.text: non-SPDX text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        license = {text="You can use it while standing on one foot"}

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license_files"] == []

    # The license text was not written
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert not license_text_file.exists()

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.text` format" in warning_text
    assert "may not be correct, and should be verified." not in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text


def test_license_pep621_text_non_spdx_multiline(tmp_path):
    """PEP 621 license.text: non-SPDX multiline text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        license = {text="You can use it\\nwhile standing on one foot"}

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license_files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert (
        license_text_file.read_text(encoding="utf-8")
        == "You can use it\nwhile standing on one foot"
    )

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.text` format" in warning_text
    assert "may not be correct, and should be verified." in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text


def test_license_pep621_file_missing_file(tmp_path):
    """PEP 621 license.file: missing file raises BriefcaseConfigError at parse time."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        """,
    )
    # Do NOT create the LICENSE file.

    with pytest.raises(
        BriefcaseConfigError,
        match=r"The PEP 621 license.file 'LICENSE' for 'my_app' does not exist",
    ):
        parse_config(config_file, platform="macOS", output_format="app", console=Mock())


@pytest.mark.parametrize(
    "config",
    [
        # license.file in a project block
        """
        [project]
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        """,
        # license.file in a tool.briefcase block
        """
        [tool.briefcase]
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        """,
    ],
)
def test_license_pep621_file_known_spdx(config, tmp_path):
    """PEP 621 license.file: SPDX is inferred and deprecation warning issued."""
    license_text = """\
MIT License

Copyright (c) 2024 Example

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), ...
"""
    (tmp_path / "LICENSE").write_text(license_text, encoding="utf-8")

    config_file = create_file(tmp_path / "pyproject.toml", config)

    console = Mock()
    _, apps = parse_config(
        config_file, platform="macOS", output_format="app", console=console
    )

    # Unidentified license falls back to LicenseRef-UnknownLicense
    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license_files"] == ["LICENSE"]

    # One warning hinting a known license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.file` format" in warning_text
    assert "may not be correct, and should be verified." not in warning_text
    assert "LicenseRef-UnknownLicense" not in warning_text
    assert 'license = "MIT"' in warning_text
    assert "should not release your project without resolving" in warning_text


def test_license_pep621_file_unknown_spdx(tmp_path):
    """PEP 621 license.file: unknown SPDX falls back to LicenseRef-UnknownLicense."""
    (tmp_path / "LICENSE").write_text(
        "This is a totally custom license with no SPDX match.", encoding="utf-8"
    )

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file, platform="macOS", output_format="app", console=console
    )

    # Unidentified license falls back to LicenseRef-UnknownLicense
    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license_files"] == ["LICENSE"]

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.file` format" in warning_text
    assert "may not be correct, and should be verified." not in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text


def test_license_pep621_file_unknown_key(tmp_path):
    """PEP 621 license table with unknown key raises error."""
    create_file(tmp_path / "LICENSE", "MIT License.")
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license.unknown = "something"

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"defines an invalid PEP 621\n`license` table",
    ):
        parse_config(config_file, platform="macOS", output_format="app", console=Mock())


def test_license_pep621_table_multiple_keys(tmp_path):
    """PEP 621 license table with multiple keys raises an error."""
    create_file(tmp_path / "LICENSE", "MIT License.")
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [project.license]
        text = "MIT License"
        file = "LICENSE"

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"defines an invalid PEP 621\n`license` table",
    ):
        parse_config(config_file, platform="macOS", output_format="app", console=Mock())


@pytest.mark.parametrize(
    "config",
    [
        # license in a project block
        """
        [project]
        license = "MIT License text"

        [tool.briefcase.app.my_app]
        """,
        # license in a tool.briefcase block
        """
        [tool.briefcase]
        license = "MIT License text"

        [tool.briefcase.app.my_app]
        """,
    ],
)
def test_license_text_spdx(config, tmp_path):
    """Pre-PEP 621 license: recognizable SPDX text is coerced."""
    config_path = create_file(tmp_path / "pyproject.toml", config)

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license_files"] == []

    # The license text was not written
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert not license_text_file.exists()

    # One warning hinting a known license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses pre-PEP 621 `license` format" in warning_text
    assert "may not be correct, and should be verified." not in warning_text
    assert "LicenseRef-UnknownLicense" not in warning_text
    assert 'license = "MIT"' in warning_text


def test_license_text_non_spdx(tmp_path):
    """Pre-PEP 621 license: non-SPDX text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "awesome"
        version = "1.2.3"
        description = "awesome project"
        license = "You can use it while standing on one foot"

        [tool.briefcase]
        project_name = "Awesome app"
        bundle = "com.example"

        [tool.briefcase.app.my_app]
        sources = ["src"]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license_files"] == []

    # The license text was not written
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert not license_text_file.exists()

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses pre-PEP 621 `license` format" in warning_text
    assert "may not be correct, and should be verified." not in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text


def test_license_text_non_spdx_multiline(tmp_path):
    """Pre-PEP 621 license: non-SPDX multiline text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "awesome"
        version = "1.2.3"
        description = "awesome project"
        license = "You can use it\\nwhile standing on one foot"

        [tool.briefcase]
        project_name = "Awesome app"
        bundle = "com.example"

        [tool.briefcase.app.my_app]
        sources = ["src"]
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_path,
        platform="macOS",
        output_format="app",
        console=console,
    )

    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license_files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert (
        license_text_file.read_text(encoding="utf-8")
        == "You can use it\nwhile standing on one foot"
    )

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses pre-PEP 621 `license` format" in warning_text
    assert "may not be correct, and should be verified." in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text


def test_no_license_key(tmp_path):
    """An app without a license key gets dummy values and a warning."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"does not contain a valid PEP 639 license definition",
    ):
        parse_config(
            config_file,
            platform="macOS",
            output_format="Xcode",
            console=Mock(),
        )


def test_pep621_empty_dynamic(monkeypatch, tmp_path):
    "A configuration with an empty dynamic property list can be handled."
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        dynamic = []
        name = "awesome"
        version = "1.2.3"
        license = "EUPL-1.2"

        [tool.briefcase]
        bundle = "com.example"

        [tool.briefcase.app.awesome]
        formal_name = "Awesome Application"
        long_description = "The application is very awesome"
        """,
    )

    wheel_metadata = Mock()
    monkeypatch.setattr("briefcase.config.project_wheel_metadata", wheel_metadata)

    # Parse config
    _, apps = parse_config(
        config_file,
        platform="linux",
        output_format="app",
        console=Mock(),
    )

    # Wheel metadata was *not* evaluated
    wheel_metadata.assert_not_called()

    # Final metadata is as expected
    awesome = apps["awesome"]
    assert awesome == {
        "app_name": "awesome",
        "bundle": "com.example",
        "version": "1.2.3",
        "license": "EUPL-1.2",
        "license_files": [],
        "formal_name": "Awesome Application",
        "long_description": "The application is very awesome",
    }


def test_pep621_dynamic(monkeypatch, tmp_path):
    "A project with dynamic metadata uses the PEP 517 build-system interface."
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"

        [project]
        dynamic = [
            "authors",
            "dependencies",
            "description",
            "license",
            "urls",
            "version"
        ]
        name = "awesome"

        [tool.hatch.metadata.hooks.custom]

        [tool.briefcase]
        bundle = "com.example"

        [tool.briefcase.app.awesome]
        formal_name = "Awesome Application"
        """,
    )

    metadata = Message()
    metadata["Metadata-Version"] = "2.4"
    metadata["Name"] = "awesome"
    metadata["Version"] = "1.2.3"
    metadata["Summary"] = "The application is very awesome"
    metadata["Project-URL"] = "Docs, https://example.com/docs"
    metadata["Project-URL"] = "Homepage, https://example.com/"
    metadata["Author-email"] = "Kim Park <kim@example.com>, John Doe <john@example.org>"
    metadata["License-Expression"] = "GPL-3.0"
    metadata["Requires-Dist"] = "toga>=0.5.3"

    wheel_metadata = Mock(return_value=metadata)
    monkeypatch.setattr("briefcase.config.project_wheel_metadata", wheel_metadata)

    # Parse config
    _, apps = parse_config(
        config_file,
        platform="linux",
        output_format="app",
        console=Console(),
    )

    # Wheel metadata was evaluated
    wheel_metadata.assert_called_once_with(tmp_path, isolated=True)

    # Final app properties are as expected
    awesome = apps["awesome"]
    assert awesome == {
        "app_name": "awesome",
        "author": "Kim Park",
        "author_email": "kim@example.com",
        "bundle": "com.example",
        "description": "The application is very awesome",
        "formal_name": "Awesome Application",
        "license": "GPL-3.0",
        "license_files": [],
        "requires": ["toga>=0.5.3"],
        "url": "https://example.com/",
        "version": "1.2.3",
    }


def test_pep621_dynamic_error(monkeypatch, tmp_path):
    "An error processing dynamic PEP 621 metadata is raised to the user."
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [build-system]
        requires = ["pdm-backend"]
        build-backend = "not_installed.backend"

        [project]
        dynamic = ["license"]
        name = "awesome"
        description = "The application is very awesome"

        [tool.pdm.version]
        source = "call"
        getter = "awesome:version"

        [tool.briefcase]
        bundle = "com.example"

        [tool.briefcase.app.awesome]
        formal_name = "Awesome Application"
        """,
    )

    monkeypatch.setattr(
        "briefcase.config.project_wheel_metadata",
        Mock(side_effect=BuildBackendException(ValueError())),
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"unable to resolve dynamic PEP 621 metadata for your project",
    ):
        parse_config(
            config_file,
            platform="linux",
            output_format="app",
            console=Console(),
        )


def test_pep621_backend_error(monkeypatch, tmp_path):
    "An error running the build backend is raised to the user."
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [build-system]
        requires = ["no-such-backend"]
        build-backend = "not_installed.backend"

        [project]
        dynamic = ["license"]
        name = "awesome"
        description = "The application is very awesome"

        [tool.pdm.version]
        source = "call"
        getter = "awesome:version"

        [tool.briefcase]
        bundle = "com.example"

        [tool.briefcase.app.awesome]
        formal_name = "Awesome Application"
        """,
    )

    monkeypatch.setattr(
        "briefcase.config.project_wheel_metadata",
        Mock(side_effect=subprocess.CalledProcessError("python -m build", 1)),
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"unable to run the PEP 517 build interface for your project",
    ):
        parse_config(
            config_file,
            platform="linux",
            output_format="app",
            console=Console(),
        )
