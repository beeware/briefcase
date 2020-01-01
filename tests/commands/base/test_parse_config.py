
import pytest

from briefcase.exceptions import BriefcaseConfigError


def test_missing_config(base_command):
    "If the configuration file doesn't exit, raise an error"
    filename = str(base_command.base_path / 'does_not_exist.toml')
    with pytest.raises(BriefcaseConfigError, match="configuration file not found"):
        base_command.parse_config(filename)


def test_incomplete_global_config(base_command):
    "If the global configuration is missing a required argument, an error is raised"
    # Provide a configuration that is missing `bundle`, a required attribute
    filename = str(base_command.base_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        version = "1.2.3"
        description = "A sample app"

        [tool.briefcase.app.my-app]
    """)

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Global configuration is incomplete \(missing 'bundle', 'project_name'\)"
    ):
        base_command.parse_config(filename)


def test_incomplete_config(base_command):
    "If the configuration is missing a required argument, an error is raised"
    # Provide a configuration that is missing `bundle`, a required attribute
    filename = str(base_command.base_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        project_name = "Sample project"
        version = "1.2.3"
        bundle = "com.example"
        description = "A sample app"

        [tool.briefcase.app.my-app]
    """)

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Configuration for 'my-app' is incomplete \(missing 'sources'\)"
    ):
        base_command.parse_config(filename)


def test_parse_config(base_command):
    "A well formed configuration file can be augmented by the command line"
    filename = str(base_command.base_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        project_name = "Sample project"
        version = "1.2.3"
        description = "A sample app"
        bundle = "org.beeware"
        mystery = 'default'

        [tool.briefcase.app.firstapp]
        sources = ['src/firstapp']

        [tool.briefcase.app.secondapp]
        sources = ['src/secondapp']
        extra = 'something'
        mystery = 'sekrits'
    """)

    # Parse the configuration
    base_command.parse_config(filename)

    # There is a global configuration object
    assert repr(base_command.global_config) == '<Sample project v1.2.3 GlobalConfig>'
    assert base_command.global_config.project_name == 'Sample project'
    assert base_command.global_config.bundle == 'org.beeware'
    assert base_command.global_config.version == '1.2.3'

    # The first app will have all the base attributes required by an app,
    # defined in the config file.
    assert repr(base_command.apps['firstapp']) == '<org.beeware.firstapp v1.2.3 AppConfig>'
    assert base_command.apps['firstapp'].project_name == 'Sample project'
    assert base_command.apps['firstapp'].app_name == 'firstapp'
    assert base_command.apps['firstapp'].bundle == 'org.beeware'
    assert base_command.apps['firstapp'].mystery == 'default'
    assert not hasattr(base_command.apps['firstapp'], 'extra')

    # The second app is much the same, except that it has an override
    # value for `mystery`, and an `extra` value.
    assert repr(base_command.apps['secondapp']) == '<org.beeware.secondapp v1.2.3 AppConfig>'
    assert base_command.apps['secondapp'].project_name == 'Sample project'
    assert base_command.apps['secondapp'].app_name == 'secondapp'
    assert base_command.apps['secondapp'].bundle == 'org.beeware'
    assert base_command.apps['secondapp'].mystery == 'sekrits'
    assert base_command.apps['secondapp'].extra == 'something'


def test_parse_config_custom_config_classes_missing_global_arg(other_command):
    "A command that defines custom config classes can enforce global arguments"
    filename = str(other_command.base_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        version = "1.2.3"
        description = "A sample app"
        bundle = "org.beeware"
        mystery = 'default'

        [tool.briefcase.app.firstapp]
        sources = ['src/firstapp']

    """)

    # Parse the configuration.
    # Even though the global config has everything needed for the default
    # configuration, it's missing a required option for the custom class.
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Global configuration is incomplete \(missing 'foo'\)"
    ):
        other_command.parse_config(filename)


def test_parse_config_custom_config_classes_missing_app_arg(other_command):
    "A command that defines custom config classes can enforce app arguments"
    filename = str(other_command.base_path / 'pyproject.toml')
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
        other_command.parse_config(filename)


def test_parse_config_custom_config_classes(other_command):
    "A well formed configuration file can be augmented by the command line"
    filename = str(other_command.base_path / 'pyproject.toml')
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        foo = "spam"

        [tool.briefcase.app.firstapp]
        bar = "ham"
    """)

    # Parse the configuration.
    other_command.parse_config(filename)

    # There is a custom global configuration object
    assert repr(other_command.global_config) == '<Custom GlobalConfig spam>'
    assert other_command.global_config.foo == 'spam'

    # The app will have all the base attributes required by an app,
    # defined in the config file.
    assert repr(other_command.apps['firstapp']) == '<Custom AppConfig spam, ham>'
    assert other_command.apps['firstapp'].foo == 'spam'
    assert other_command.apps['firstapp'].bar == 'ham'

    # The custom class sets the underlying attributes of the AppConfig
    assert other_command.apps['firstapp'].app_name == 'custom'
    assert other_command.apps['firstapp'].bundle == 'com.example'
    assert other_command.apps['firstapp'].version == "37.42"
