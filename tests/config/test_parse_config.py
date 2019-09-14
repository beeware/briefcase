from io import StringIO

import pytest

from briefcase.config import parse_config
from briefcase.exceptions import BriefcaseConfigError


def test_invalid_toml():
    "If the config file isn't TOML, raise an error"
    config_file = StringIO("this is not toml!")

    with pytest.raises(BriefcaseConfigError, match="Invalid pyproject.toml"):
        parse_config(config_file, platform='macos', output_format='app')


def test_no_briefcase_section():
    "If the config file doesn't contain a briefcase tool section, raise an error"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.section]
        name="value"
        number=42
        """
    )

    with pytest.raises(BriefcaseConfigError, match="No tool.briefcase section"):
        parse_config(config_file, platform='macos', output_format='app')


def test_no_apps():
    "If the config file doesn't contain at least one briefcase app, raise an error"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase]
        name="value"
        number=42
        """
    )

    with pytest.raises(BriefcaseConfigError, match="No Briefcase apps defined"):
        parse_config(config_file, platform='macos', output_format='app')


def test_single_minimal_app():
    "A single app can be defined, but can exist without any app attributes"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase]
        value = 42

        [tool.briefcase.app.my_app]
        """
    )

    global_options, apps = parse_config(config_file, platform='macos', output_format='app')

    # There's a single global option
    assert global_options == {
        'value': 42
    }

    # The app gets the name from it's header line.
    # It inherits the value from the base definition.
    assert apps == {
        'my_app': {
            "name": "my_app",
            "value": 42
        }
    }


def test_multiple_minimal_apps():
    "The configuration can contain multiple apps without an explicit tool header"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase.app.first]
        number=37

        [tool.briefcase.app.second]
        name="my_app"
        number=42
        """
    )

    global_options, apps = parse_config(config_file, platform='macos', output_format='app')

    # There are no global options
    assert global_options == {}

    # The apps gets their name from the header lines.
    # The second tool overrides it's app name
    assert apps == {
        'first': {
            "name": "first",
            "number": 37,
        },
        'second': {
            "name": "my_app",
            "number": 42,
        },
    }


def test_platform_override():
    "An app can define platform settings that override base settings"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase]
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macos]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.linux]
        value = 3
        platformvalue = "linux platform"

        [tool.briefcase.app.other_app.macos]
        value = 4
        platformvalue = "other macos platform"
        """
    )

    global_options, apps = parse_config(config_file, platform='macos', output_format='app')

    # The global options are exactly as specified
    assert global_options == {
        'value': 0,
        'basevalue': 'the base',
    }

    # Since a macOS app has been requested, the macOS platform values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Platforms should be processed in sorted order, which means that linux
    # will be processed before macos.
    assert apps == {
        'my_app': {
            "name": "my_app",
            "value": 2,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
        },
        'other_app': {
            "name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
        }
    }


def test_platform_override_ordering():
    "The order of platform processing doesn't affect output"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase]
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macos]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.windows]
        value = 3
        platformvalue = "windows platform"

        [tool.briefcase.app.other_app.macos]
        value = 4
        platformvalue = "other macos platform"
        """
    )

    global_options, apps = parse_config(config_file, platform='macos', output_format='app')

    # The global options are exactly as specified
    assert global_options == {
        'value': 0,
        'basevalue': "the base"
    }

    # Since a macOS app has been requested, the macOS platform values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Platforms should be processed in order, which means that windows
    # will be processed after macos.
    assert apps == {
        'my_app': {
            "name": "my_app",
            "value": 2,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
        },
        'other_app': {
            "name": "other_app",
            "value": 4,
            "basevalue": "the base",
            "platformvalue": "other macos platform",
        }
    }


def test_format_override():
    "An app can define format settings that override base and platform settings"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase]
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macos]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.macos.app]
        value = 21
        formatvalue = "app format"

        [tool.briefcase.app.my_app.macos.dmg]
        value = 22
        formatvalue = "dmg format"

        [tool.briefcase.app.my_app.macos.homebrew]
        value = 23
        formatvalue = "homebrew format"

        [tool.briefcase.app.my_app.linux]
        value = 3
        platformvalue = "linux platform"

        [tool.briefcase.app.my_app.linux.snap]
        value = 31
        formatvalue = "snap format"

        [tool.briefcase.app.my_app.linux.appimage]
        value = 32
        formatvalue = "appimage format"

        [tool.briefcase.app.other_app.macos.app]
        value = 41
        formatvalue = "other macos app format"
        """
    )

    global_options, apps = parse_config(config_file, platform='macos', output_format='app')

    # The global options are exactly as specified
    assert global_options == {
        'value': 0,
        'basevalue': "the base"
    }

    # Since a macOS app has been requested, the macOS app format values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Formats should be processed in order, which means that app
    # will be processed before dmg and homebrew.
    assert apps == {
        'my_app': {
            "name": "my_app",
            "value": 21,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
            "formatvalue": "app format",
        },
        'other_app': {
            "name": "other_app",
            "value": 41,
            "basevalue": "the base",
            "formatvalue": "other macos app format",
        }
    }


def test_format_override_ordering():
    "The order of format processing doesn't affect output"
    config_file = StringIO(
        """
        [build-system]
        requires = ["briefcase"]

        [tool.briefcase]
        value = 0
        basevalue = "the base"

        [tool.briefcase.app.my_app]
        value = 1
        appvalue = "the app"

        [tool.briefcase.app.my_app.macos]
        value = 2
        platformvalue = "macos platform"

        [tool.briefcase.app.my_app.macos.app]
        value = 21
        formatvalue = "app format"

        [tool.briefcase.app.my_app.macos.dmg]
        value = 22
        formatvalue = "dmg format"

        [tool.briefcase.app.my_app.macos.homebrew]
        value = 23
        formatvalue = "homebrew format"

        [tool.briefcase.app.my_app.linux]
        value = 3
        platformvalue = "linux platform"

        [tool.briefcase.app.my_app.linux.snap]
        value = 31
        formatvalue = "snap format"

        [tool.briefcase.app.my_app.linux.appimage]
        value = 32
        formatvalue = "appimage format"

        [tool.briefcase.app.other_app.macos.app]
        value = 41
        formatvalue = "other macos app format"
        """
    )

    global_options, apps = parse_config(config_file, platform='macos', output_format='dmg')

    # The global options are exactly as specified
    assert global_options == {
        'value': 0,
        'basevalue': "the base"
    }

    # Since a macOS dmg has been requested, the macOS dmg format values
    # take priority. Linux configuration values are dropped.
    # The second app doesn't provide an explicit app-level config, but
    # the app exists because the platform exists.
    # Formats should be processed in order, which means that dmg
    # will be processed after app, but before homebrew.
    assert apps == {
        'my_app': {
            "name": "my_app",
            "value": 22,
            "basevalue": "the base",
            "appvalue": "the app",
            "platformvalue": "macos platform",
            "formatvalue": "dmg format",
        },
        'other_app': {
            "name": "other_app",
            "value": 0,
            "basevalue": "the base",
        }
    }
