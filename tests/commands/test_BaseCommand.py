import argparse

import pytest

from briefcase.commands import BaseCommand
from briefcase.exceptions import BriefcaseConfigError


class DummyCommand(BaseCommand):
    """
    A dummy command to test the BaseCommand interface.

    Defines a mix of configuration and non-configuration options,
    some of which have default values.
    """
    def __init__(self, extra=None):
        parser = argparse.ArgumentParser()
        super().__init__(
            platform='macos',
            output_format='app',
            parser=parser,
            extra=() if extra is None else extra
        )

    def add_options(self, parser):
        # Provide 4 extra arguments:
        # * a normal argument that will have a value provided
        parser.add_argument('-x', '--extra')
        # * an argument that won't have a value provided
        parser.add_argument('-m', '--mystery')
        # * an argument that won't have a value provided, but has a default
        parser.add_argument('-d', '--default', default='deefawlt')
        # * an argument that isn't an app config option.
        parser.add_argument('-o', '--output')

    @property
    def config_options(self):
        # Include all the options *except* output.
        return super().config_options.union({'extra', 'mystery', 'default'})


def test_missing_config(tmp_path):
    "If the configuration file doesn't exit, raise an error"
    command = DummyCommand(extra=('-x', 'wibble', '-o', 'somewhere'))

    filename = tmp_path / 'does_not_exist.toml'
    with pytest.raises(BriefcaseConfigError, match="configuration file not found"):
        command.parse_config(filename)


def test_incomplete_config(tmp_path):
    "If the configuration is missing a required argument, an error is raised"
    command = DummyCommand(extra=('-x', 'wibble', '-o', 'somewhere'))

    # Provide a configuration that is missing `bundle`, a required attribute
    filename = tmp_path / 'pyproject.toml'
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
    command = DummyCommand(extra=('-x', 'wibble', '-o', 'somewhere'))

    # As a result of constructing the command,
    # the command options have been parsed
    assert command.options.extra == "wibble"
    assert command.options.default == "deefawlt"
    assert command.options.output == "somewhere"

    filename = tmp_path / 'pyproject.toml'
    with open(filename, 'w') as config_file:
        config_file.write("""
        [tool.briefcase]
        version = "1.2.3"
        bundle = "org.beeware"

        [tool.briefcase.app.firstapp]

        [tool.briefcase.app.secondapp]
        extra = 'something'
        default = 'special'
    """)

    command.parse_config(filename)

    # The first app will have:
    # * all the base attributes required by an app, defined in the file
    # * a value for the `extra` argument provided at the command line.
    # * a default value for the `default` argument that wasn't specified
    # * a `None` value for the unspecified `mystery` argument
    # * No representation of the output argument, which wasn't flagged as
    #   a config argument.
    assert repr(command.apps['firstapp']) == '<AppConfig org.beeware.firstapp v1.2.3>'
    assert command.apps['firstapp'].name == 'firstapp'
    assert command.apps['firstapp'].bundle == 'org.beeware'
    assert command.apps['firstapp'].extra == 'wibble'
    assert command.apps['firstapp'].default == 'deefawlt'
    assert command.apps['firstapp'].mystery is None
    assert not hasattr(command.apps['firstapp'], 'output')

    # The second app is much the same; however, as it provides an
    # *explicit* value for default, that value takes priority over
    # the default command line value. The value for extra *is* overwritten,
    # as it was explicitly provided at the command line.
    assert repr(command.apps['secondapp']) == '<AppConfig org.beeware.secondapp v1.2.3>'
    assert command.apps['secondapp'].name == 'secondapp'
    assert command.apps['secondapp'].bundle == 'org.beeware'
    assert command.apps['secondapp'].extra == 'wibble'
    assert command.apps['secondapp'].default == 'special'
    assert command.apps['secondapp'].mystery is None
    assert not hasattr(command.apps['secondapp'], 'output')
