import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_single_source(base_command, myapp):
    "If an app provides a single source location and it matches, it is selected as the dist-info location"
    myapp.sources = ['src/my_app']

    assert str(base_command.app_module_path(myapp)) == str(base_command.base_path / 'src' / 'my_app')


def test_matching_source(base_command, myapp):
    "If an app provides a single matching source location, it is selected as the dist-info location"
    myapp.sources = ['src/other', 'src/my_app', 'src/extra']

    assert str(base_command.app_module_path(myapp)) == str(base_command.base_path / 'src' / 'my_app')


def test_multiple_match(base_command, myapp):
    "If an app provides multiple matching source location, it is selected as the dist-info location"
    myapp.sources = ['src/my_app', 'extra/my_app']

    with pytest.raises(BriefcaseCommandError):
        base_command.app_module_path(myapp)


def test_hyphen_source(base_command, myapp):
    "If an app provides a single matching source location, it is selected as the dist-info location"
    myapp.sources = ['src/my-app']

    with pytest.raises(BriefcaseCommandError):
        base_command.app_module_path(myapp)


def test_no_match(base_command, myapp):
    "If an app provides a single matching source location, it is selected as the dist-info location"
    myapp.sources = ['src/pork', 'src/spam']

    with pytest.raises(BriefcaseCommandError):
        base_command.app_module_path(myapp)
