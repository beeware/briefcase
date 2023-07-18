import pytest

from briefcase.exceptions import BriefcaseConfigError

from ...utils import create_file


def test_missing_config(base_command):
    """If the configuration file doesn't exit, raise an error."""
    filename = base_command.base_path / "does_not_exist.toml"
    with pytest.raises(BriefcaseConfigError, match="Configuration file not found"):
        base_command.parse_config(filename)


def test_incomplete_global_config(base_command):
    """If the global configuration is missing a required argument, an error is
    raised."""
    # Provide a configuration that is missing `bundle`, a required attribute
    filename = base_command.base_path / "pyproject.toml"
    create_file(
        filename,
        """
        [tool.briefcase]
        version = "1.2.3"
        description = "A sample app"

        [tool.briefcase.app.my-app]
    """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Global configuration is incomplete \(missing 'bundle', 'project_name'\)",
    ):
        base_command.parse_config(filename)


def test_incomplete_config(base_command):
    """If the configuration is missing a required argument, an error is raised."""
    # Provide a configuration that is missing `bundle`, a required attribute
    filename = base_command.base_path / "pyproject.toml"
    create_file(
        filename,
        """
        [tool.briefcase]
        project_name = "Sample project"
        version = "1.2.3"
        bundle = "com.example"
        description = "A sample app"

        [tool.briefcase.app.my-app]
    """,
    )

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Configuration for 'my-app' is incomplete \(missing 'sources'\)",
    ):
        base_command.parse_config(filename)


def test_parse_config(base_command):
    """A well-formed configuration file can be augmented by the command line."""
    filename = base_command.base_path / "pyproject.toml"
    create_file(
        filename,
        """
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
    """,
    )

    # Parse the configuration
    base_command.parse_config(filename)

    # There is a global configuration object
    assert repr(base_command.global_config) == "<Sample project v1.2.3 GlobalConfig>"
    assert base_command.global_config.project_name == "Sample project"
    assert base_command.global_config.bundle == "org.beeware"
    assert base_command.global_config.version == "1.2.3"

    # The first app will have all the base attributes required by an app,
    # defined in the config file.
    assert (
        repr(base_command.apps["firstapp"]) == "<org.beeware.firstapp v1.2.3 AppConfig>"
    )
    assert base_command.apps["firstapp"].project_name == "Sample project"
    assert base_command.apps["firstapp"].app_name == "firstapp"
    assert base_command.apps["firstapp"].bundle == "org.beeware"
    assert base_command.apps["firstapp"].mystery == "default"
    assert not hasattr(base_command.apps["firstapp"], "extra")

    # The second app is much the same, except that it has an override
    # value for `mystery`, and an `extra` value.
    assert (
        repr(base_command.apps["secondapp"])
        == "<org.beeware.secondapp v1.2.3 AppConfig>"
    )
    assert base_command.apps["secondapp"].project_name == "Sample project"
    assert base_command.apps["secondapp"].app_name == "secondapp"
    assert base_command.apps["secondapp"].bundle == "org.beeware"
    assert base_command.apps["secondapp"].mystery == "sekrits"
    assert base_command.apps["secondapp"].extra == "something"
