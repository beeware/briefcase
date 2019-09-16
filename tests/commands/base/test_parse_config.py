
import pytest

from briefcase.commands.base import BaseCommand
from briefcase.config import GlobalConfig, AppConfig
from briefcase.exceptions import BriefcaseConfigError


class DummyCommand(BaseCommand):
    """
    A dummy command to test the BaseCommand interface.
    """
    def __init__(self):
        super().__init__(platform='tester', output_format='dummy')

    def bundle_path(self, app, base=None):
        raise NotImplementedError()

    def binary_path(self, app, base=None):
        raise NotImplementedError()


class CustomGlobalConfig(GlobalConfig):
    def __init__(self, foo, **kwargs):
        super().__init__(**kwargs)
        self.foo = foo

    def __repr__(self):
        return '<Custom GlobalConfig {foo}>'.format(foo=self.foo)


class CustomAppConfig(AppConfig):
    def __init__(self, foo, bar, **kwargs):
        super().__init__(name='custom', bundle='com.example', version=42)
        self.foo = foo
        self.bar = bar

    def __repr__(self):
        return '<Custom AppConfig {foo}, {bar}>'.format(
            foo=self.foo,
            bar=self.bar
        )


class CustomConfigDummyCommand(DummyCommand):
    GLOBAL_CONFIG_CLASS = CustomGlobalConfig
    APP_CONFIG_CLASS = CustomAppConfig


def test_missing_config(tmp_path):
    "If the configuration file doesn't exit, raise an error"
    command = DummyCommand()

    filename = str(tmp_path / 'does_not_exist.toml')
    with pytest.raises(BriefcaseConfigError, match="configuration file not found"):
        command.parse_config(filename)


def test_incomplete_config(tmp_path):
    "If the configuration is missing a required argument, an error is raised"
    command = DummyCommand()

    # Provide a configuration that is missing `bundle`, a required attribute
    filename = str(tmp_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        version = "1.2.3"

        [tool.briefcase.app.myapp]
    """)

    with pytest.raises(BriefcaseConfigError, match=r"Configuration for 'myapp' is incomplete \(missing 'bundle'\)"):
        command.parse_config(filename)


def test_parse_config(tmp_path):
    "A well formed configuration file can be augmented by the command line"
    command = DummyCommand()

    filename = str(tmp_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        version = "1.2.3"
        bundle = "org.beeware"
        mystery = 'default'

        [tool.briefcase.app.firstapp]

        [tool.briefcase.app.secondapp]
        extra = 'something'
        mystery = 'sekrits'
    """)

    # Parse the configuration
    command.parse_config(filename)

    # There is a global configuration object
    assert repr(command.global_config) == '<GlobalConfig>'
    assert command.global_config.bundle == 'org.beeware'
    assert command.global_config.version == '1.2.3'

    # The first app will have all the base attributes required by an app,
    # defined in the config file.
    assert repr(command.apps['firstapp']) == '<AppConfig org.beeware.firstapp v1.2.3>'
    assert command.apps['firstapp'].name == 'firstapp'
    assert command.apps['firstapp'].bundle == 'org.beeware'
    assert command.apps['firstapp'].mystery == 'default'
    assert not hasattr(command.apps['firstapp'], 'extra')

    # The second app is much the same, except that it has an override
    # value for `mystery`, and an `extra` value.
    assert repr(command.apps['secondapp']) == '<AppConfig org.beeware.secondapp v1.2.3>'
    assert command.apps['secondapp'].name == 'secondapp'
    assert command.apps['secondapp'].bundle == 'org.beeware'
    assert command.apps['secondapp'].mystery == 'sekrits'
    assert command.apps['secondapp'].extra == 'something'


def test_parse_config_custom_config_classes_missing_global_arg(tmp_path):
    "A command that defines custom config classes can enforce global arguments"
    command = CustomConfigDummyCommand()

    filename = str(tmp_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        version = "1.2.3"
        bundle = "org.beeware"
        mystery = 'default'

        [tool.briefcase.app.firstapp]

    """)

    # Parse the configuration.
    # Even though the global config has everything needed for the default
    # configuration, it's missing a required option for the custom class.
    with pytest.raises(BriefcaseConfigError, match=r"Global configuration is incomplete \(missing 'foo'\)"):
        command.parse_config(filename)


def test_parse_config_custom_config_classes_missing_app_arg(tmp_path):
    "A command that defines custom config classes can enforce app arguments"
    command = CustomConfigDummyCommand()

    filename = str(tmp_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        foo = "spam"

        [tool.briefcase.app.firstapp]

    """)

    # Parse the configuration.
    # Even though the app config has everything needed for the default
    # configuration, it's missing a required option for the custom class.
    with pytest.raises(BriefcaseConfigError, match=r"Configuration for 'firstapp' is incomplete \(missing 'bar'\)"):
        command.parse_config(filename)


def test_parse_config_custom_config_classes(tmp_path):
    "A well formed configuration file can be augmented by the command line"
    command = CustomConfigDummyCommand()

    filename = str(tmp_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        foo = "spam"

        [tool.briefcase.app.firstapp]
        bar = "ham"
    """)

    # Parse the configuration.
    command.parse_config(filename)

    # There is a custom global configuration object
    assert repr(command.global_config) == '<Custom GlobalConfig spam>'
    assert command.global_config.foo == 'spam'

    # The app will have all the base attributes required by an app,
    # defined in the config file.
    assert repr(command.apps['firstapp']) == '<Custom AppConfig spam, ham>'
    assert command.apps['firstapp'].foo == 'spam'
    assert command.apps['firstapp'].bar == 'ham'

    # The custom class sets the underlying attributes of the AppConfig
    assert command.apps['firstapp'].name == 'custom'
    assert command.apps['firstapp'].bundle == 'com.example'
    assert command.apps['firstapp'].version == 42
