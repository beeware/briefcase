from briefcase.config import AppConfig

import pytest


def test_minimal_AppConfig():
    "A simple config can be defined"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
    )

    # Requests for an icon or splash raises an attribute error
    with pytest.raises(AttributeError, match="'AppConfig' object has no attribute 'icon'"):
        config.icon

    with pytest.raises(AttributeError, match="'AppConfig' object has no attribute 'icon'"):
        config.has_scaled_icon

    with pytest.raises(AttributeError, match="'AppConfig' object has no attribute 'splash'"):
        config.splash

    with pytest.raises(AttributeError, match="'AppConfig' object has no attribute 'splash'"):
        config.has_scaled_splash

    assert repr(config) == "<AppConfig org.beeware.myapp v1.2.3>"


def test_extra_attrs():
    "A config can contain attributes in addition to those required"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        first="value 1",
        second=42,
    )

    assert config.first == "value 1"
    assert config.second == 42

    # An attribute that wasn't provided raises an error
    with pytest.raises(AttributeError):
        config.unknown


def test_config_with_simple_icon():
    "A config can specify a single icon file"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        icon='myicon.png',
    )

    assert not config.has_scaled_icon
    assert config.icon == 'myicon.png'


def test_config_with_sized_icon():
    "A config can specify multiple icon sizes (using int or str)"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        icon={
            72: 'myicon-72.png',
            '144': 'myicon-144.png',
        }
    )

    assert config.has_scaled_icon

    # Icons can be retrieved using a size
    assert config.icon['72'] == 'myicon-72.png'
    assert config.icon['144'] == 'myicon-144.png'

    # An unknown icon size raises an error
    with pytest.raises(KeyError):
        config.icon['512']


def test_config_with_simple_splash():
    "A config can specify a single splash file"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        splash='mysplash.png',
    )

    assert not config.has_scaled_splash
    assert config.splash == 'mysplash.png'


def test_config_with_sized_splash():
    "A config can specify multiple splash sizes (using int or str)"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        splash={
            '640x1136': 'portrait.png',
            '1136x640': 'landscape.png',
        }
    )

    assert config.has_scaled_splash

    # The splash can be retrieved using a size
    assert config.splash['640x1136'] == 'portrait.png'
    assert config.splash['1136x640'] == 'landscape.png'

    # An unknown splash size raises an error
    with pytest.raises(KeyError):
        config.splash['1234x4321']
