from io import BytesIO

import pytest

from briefcase.config import parse_config
from briefcase.exceptions import BriefcaseConfigError


def test_invalid_toml():
    """If the config file isn't TOML, raise an error."""
    config_file = BytesIO(b"this is not toml!")

    with pytest.raises(BriefcaseConfigError, match="Invalid pyproject.toml"):
        parse_config(config_file, platform="macOS", output_format="Xcode")


def test_no_briefcase_section():
    """If the config file doesn't contain a briefcase tool section, raise an error."""
    config_file = BytesIO(
        b"""
        [tool.section]
        name="value"
        number=42
        """
    )

    with pytest.raises(BriefcaseConfigError, match="No tool.briefcase section"):
        parse_config(config_file, platform="macOS", output_format="Xcode")


def test_no_apps():
    """If the config file doesn't contain at least one briefcase app, raise an error."""
    config_file = BytesIO(
        b"""
        [tool.briefcase]
        name="value"
        number=42
        """
    )

    with pytest.raises(BriefcaseConfigError, match="No Briefcase apps defined"):
        parse_config(config_file, platform="macOS", output_format="Xcode")


def test_single_minimal_app():
    """A single app can be defined, but can exist without any app attributes."""
    config_file = BytesIO(
        b"""
        [tool.briefcase]
        value = 42

        [tool.briefcase.app.my_app]
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="Xcode"
    )

    # There's a single global option
    assert global_options == {"value": 42}

    # The app gets the name from its header line.
    # It inherits the value from the base definition.
    assert apps == {"my_app": {"app_name": "my_app", "value": 42}}


def test_multiple_minimal_apps():
    """The configuration can contain multiple apps without an explicit tool header."""
    config_file = BytesIO(
        b"""
        [tool.briefcase.app.first]
        number=37

        [tool.briefcase.app.second]
        app_name="my_app"
        number=42
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="Xcode"
    )

    # There are no global options
    assert global_options == {}

    # The apps get their name from the header lines.
    # The second tool overrides its app name
    assert apps == {
        "first": {
            "app_name": "first",
            "number": 37,
        },
        "second": {
            "app_name": "my_app",
            "number": 42,
        },
    }


def test_platform_override():
    """An app can define platform settings that override base settings."""
    config_file = BytesIO(
        b"""
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
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="Xcode"
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
        },
        "other_app": {
            "app_name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
        },
    }


def test_platform_override_ordering():
    """The order of platform processing doesn't affect output."""
    config_file = BytesIO(
        b"""
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
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="Xcode"
    )

    # The global options are exactly as specified
    assert global_options == {"value": 0, "basevalue": "the base"}

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
        },
        "other_app": {
            "app_name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
        },
    }


def test_format_override():
    """An app can define format settings that override base and platform settings."""
    config_file = BytesIO(
        b"""
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
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="app"
    )

    # The global options are exactly as specified
    assert global_options == {"value": 0, "basevalue": "the base"}

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
        },
        "other_app": {
            "app_name": "other_app",
            "value": 41,
            "basevalue": "the base",
            "formatvalue": "other macos app format",
        },
    }


def test_format_override_ordering():
    """The order of format processing doesn't affect output."""
    config_file = BytesIO(
        b"""
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
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="app"
    )

    # The global options are exactly as specified
    assert global_options == {"value": 0, "basevalue": "the base"}

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
        },
        "other_app": {
            "app_name": "other_app",
            "value": 0,
            "basevalue": "the base",
        },
    }


def test_requires():
    """Requirements can be specified."""
    config_file = BytesIO(
        b"""
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
        """
    )

    # Request a macOS app
    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="app"
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
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
        },
    }

    # Request a macOS xcode project
    config_file.seek(0)
    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="Xcode"
    )

    # The global options are exactly as specified
    assert global_options == {"value": 0, "requires": ["base value"]}

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
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
        },
    }

    config_file.seek(0)
    global_options, apps = parse_config(
        config_file, platform="linux", output_format="appimage"
    )

    # The global options are exactly as specified
    assert global_options == {"value": 0, "requires": ["base value"]}

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
        },
        "other_app": {
            "app_name": "other_app",
            "requires": [
                "base value",
            ],
            "value": 0,
        },
    }


def test_document_types():
    """Document types can be specified."""
    config_file = BytesIO(
        b"""
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

        """
    )

    # Request a macOS app
    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="Xcode"
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
        },
        "other_app": {
            "app_name": "other_app",
            "value": 0,
        },
    }


def test_pep621_defaults():
    config_file = BytesIO(
        b"""
        [project]
        name = "awesome"
        version = "1.2.3"
        authors = [{name = "Kim Park", email = "kim@example.com"}]
        dependencies = ["numpy"]
        description = "awesome project"

        [project.urls]
        Homepage = "https://example.com/awesome"

        [project.optional-dependencies]
        test = ["pytest"]

        [project.license]
        text = "You can use it while standing on one foot"

        [tool.briefcase]
        project_name = "Awesome app"
        bundle = "com.example"

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
            "std-nslog~=1.0.0"
        ]
        """
    )

    global_options, apps = parse_config(
        config_file, platform="macOS", output_format="app"
    )

    awesome = apps["awesome"]
    assert awesome == {
        "project_name": "Awesome app",
        "bundle": "com.example",
        "version": "1.2.3",
        "license": "You can use it while standing on one foot",
        "author": "Kim Park",
        "author_email": "kim@example.com",
        "url": "https://example.com/awesome",
        "description": "awesome project",
        "requires": ["numpy", "toga-cocoa~=0.3.1", "std-nslog~=1.0.0"],
        "test_requires": ["pytest"],
        "app_name": "awesome",
        "sources": ["src"],
        "test_sources": ["tests"],
        "formal_name": "Awesome Application",
        "long_description": "The application is very awesome",
    }
