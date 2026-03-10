from unittest.mock import Mock

import pytest

from briefcase.config import parse_config
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

    # There's a single global option
    assert global_options == {
        "value": 42,
    }

    # The app gets the name from its header line.
    # It inherits the value from the base definition.
    # It gets a guess at a license
    assert apps == {
        "my_app": {
            "app_name": "my_app",
            "value": 42,
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        }
    }

    # Both apps have no license definition; a warning should be emitted for each.
    assert console.warning.call_count == 1
    first_warning = console.warning.call_args_list[0][0][0]
    assert "WARNING: 'my_app' does not define a license" in first_warning


def test_multiple_minimal_apps(tmp_path):
    """The configuration can contain multiple apps without an explicit tool header."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase.app.first]
        number=37

        [tool.briefcase.app.second]
        number=42
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.first.txt"],
        },
        "second": {
            "app_name": "second",
            "number": 42,
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.second.txt"],
        },
    }

    # Both apps have no license definition; a warning should be emitted for each.
    assert console.warning.call_count == 2
    first_warning = console.warning.call_args_list[0][0][0]
    assert "WARNING: 'first' does not define a license" in first_warning
    second_warning = console.warning.call_args_list[1][0][0]
    assert "WARNING: 'second' does not define a license" in second_warning


def test_platform_override(tmp_path):
    """An app can define platform settings that override base settings."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
        },
    }


def test_format_override(tmp_path):
    """An app can define format settings that override base and platform settings."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 41,
            "basevalue": "the base",
            "formatvalue": "other macos app format",
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
        },
    }


def test_format_override_ordering(tmp_path):
    """The order of format processing doesn't affect output."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 0,
            "basevalue": "the base",
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
        },
    }


def test_requires(tmp_path):
    """Requirements can be specified."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
        },
    }


def test_document_types(tmp_path):
    """Document types can be specified."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0

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
    _global_options, apps = parse_config(
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
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.my_app.txt"],
        },
        "other_app": {
            "app_name": "other_app",
            "value": 0,
            "license": "LicenseRef-UnknownLicense",
            "license-files": ["build/license_text.other_app.txt"],
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
        "license-files": ["LICENSE"],
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


def test_license_empty_list_is_error(tmp_path):
    """An empty license files list raises an error."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        license = "MIT"
        license-files = []

        [tool.briefcase.app.my_app]
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"empty `license-files` list",
    ):
        parse_config(
            config_file,
            platform="macOS",
            output_format="app",
            console=Mock(),
        )


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
    """A valid PEP 639 license config (string + files) is accepted without warning."""
    (tmp_path / "LICENSE").write_text("MIT License text", encoding="utf-8")

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license = "MIT"
        license-files = ["LICENSE"]

        [tool.briefcase.app.my_app]
        appvalue = "the app"
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
    assert apps["my_app"]["license-files"] == ["LICENSE"]
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
    assert apps["my_app"]["license-files"] == ["LICENSE"]
    console.warning.assert_not_called()


def test_license_pep621_text_spdx(tmp_path):
    """PEP 621 license.text: recognizable SPDX text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "awesome"
        version = "1.2.3"
        description = "awesome project"
        license.text = "MIT License text"

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

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license-files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert license_text_file.read_text(encoding="utf-8") == "MIT License text"

    # One warning hinting an identified license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.text` format" in warning_text
    assert "almost certainly incorrect" in warning_text
    assert "LicenseRef-UnknownLicense" not in warning_text
    assert 'license = "MIT"' in warning_text
    assert "should not release your project without resolving" in warning_text


def test_license_pep621_text_non_spdx(tmp_path):
    """PEP 621 license.text: non-SPDX text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "awesome"
        version = "1.2.3"
        description = "awesome project"
        license = {text="You can use it while standing on one foot"}

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
    assert apps["my_app"]["license-files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert (
        license_text_file.read_text(encoding="utf-8")
        == "You can use it while standing on one foot"
    )

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.text` format" in warning_text
    assert "almost certainly incorrect" in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text
    assert "should not release your project without resolving" in warning_text


def test_license_pep621_file_missing_file(tmp_path):
    """PEP 621 license.file: missing file raises BriefcaseConfigError at parse time."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        appvalue = "the app"
        """,
    )
    # Do NOT create the LICENSE file.

    with pytest.raises(
        BriefcaseConfigError,
        match=r"The PEP 621 license.file 'LICENSE' for 'my_app' does not exist",
    ):
        parse_config(config_file, platform="macOS", output_format="app", console=Mock())


def test_license_pep621_file_known_spdx(tmp_path):
    """PEP 621 license.file: SPDX is inferred and deprecation warning issued."""
    license_text = """\
MIT License

Copyright (c) 2024 Example

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), ...
"""
    (tmp_path / "LICENSE").write_text(license_text, encoding="utf-8")

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        appvalue = "the app"
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file, platform="macOS", output_format="app", console=console
    )

    # Unidentified license falls back to LicenseRef-UnknownLicense
    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license-files"] == ["LICENSE"]

    # One warning hinting a known license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.file` format" in warning_text
    assert "almost certainly incorrect" not in warning_text
    assert "LicenseRef-UnknownLicense" not in warning_text
    assert 'license = "MIT"' in warning_text
    assert "should not release your project without resolving" not in warning_text


def test_license_pep621_file_unknown_spdx(tmp_path):
    """PEP 621 license.file: unknown SPDX falls back to LicenseRef-UnknownLicense."""
    (tmp_path / "LICENSE").write_text(
        "This is a totally custom license with no SPDX match.", encoding="utf-8"
    )

    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license.file = "LICENSE"

        [tool.briefcase.app.my_app]
        appvalue = "the app"
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file, platform="macOS", output_format="app", console=console
    )

    # Unidentified license falls back to LicenseRef-UnknownLicense
    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license-files"] == ["LICENSE"]

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses PEP 621 `license.file` format" in warning_text
    assert "almost certainly incorrect" not in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text
    assert "should not release your project without resolving" in warning_text


def test_license_pep621_file_unknown_key(tmp_path):
    """PEP 621 license table with unknown key raises error."""
    create_file(tmp_path / "LICENSE", "MIT License.")
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0
        license.unknown = "something"

        [tool.briefcase.app.my_app]
        appvalue = "the app"
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

        [tool.briefcase]
        value = 0

        [tool.briefcase.app.my_app]
        appvalue = "the app"
        """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"defines an invalid PEP 621\n`license` table",
    ):
        parse_config(config_file, platform="macOS", output_format="app", console=Mock())


def test_license_text_spdx(tmp_path):
    """Pre-PEP 621 license: recognizable SPDX text is coerced."""
    config_path = create_file(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "awesome"
        version = "1.2.3"
        description = "awesome project"
        license = "MIT License text"

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

    assert apps["my_app"]["license"] == "MIT"
    assert apps["my_app"]["license-files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert license_text_file.read_text(encoding="utf-8") == "MIT License text"

    # One warning hinting a known license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses pre-PEP 621 `license` format" in warning_text
    assert "almost certainly incorrect" in warning_text
    assert "LicenseRef-UnknownLicense" not in warning_text
    assert 'license = "MIT"' in warning_text
    assert "should not release your project without resolving" in warning_text


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
    assert apps["my_app"]["license-files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert (
        license_text_file.read_text(encoding="utf-8")
        == "You can use it while standing on one foot"
    )

    # One warning hinting an unknown license
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "uses pre-PEP 621 `license` format" in warning_text
    assert "almost certainly incorrect" in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text
    assert "should not release your project without resolving" in warning_text


def test_no_license_key(tmp_path):
    """An app without a license key gets dummy values and a warning."""
    config_file = create_file(
        tmp_path / "pyproject.toml",
        """
        [tool.briefcase]
        value = 0

        [tool.briefcase.app.my_app]
        appvalue = "the app"
        """,
    )

    console = Mock()
    _, apps = parse_config(
        config_file,
        platform="macOS",
        output_format="app",
        console=console,
    )

    # Unidentified license falls back to LicenseRef-UnknownLicense
    assert apps["my_app"]["license"] == "LicenseRef-UnknownLicense"
    assert apps["my_app"]["license-files"] == ["build/license_text.my_app.txt"]

    # The license text was written to the expected location (global, no app suffix)
    license_text_file = tmp_path / "build" / "license_text.my_app.txt"
    assert license_text_file.exists()
    assert "Your project license should go here" in license_text_file.read_text(
        encoding="utf-8"
    )

    # One warning about the missing configuration
    console.warning.assert_called_once()
    warning_text = console.warning.call_args[0][0]
    assert "does not define a license" in warning_text
    assert "LicenseRef-UnknownLicense" in warning_text
    assert 'license = "<SPDX expression>"' in warning_text
    assert "should not release your project without resolving" in warning_text
