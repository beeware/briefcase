from unittest import mock

from ...utils import PartialMatchString


def test_question_sequence(new_command):
    """Questions are asked, a context is constructed."""

    # Prime answers for all the questions.
    new_command.console.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
    ]

    context = new_command.build_app_context(
        project_overrides={},
    )

    assert context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
        "author_email": "grace@navy.mil",
        "bundle": "org.beeware",
        "class_name": "MyApplication",
        "description": "Cool stuff",
        "formal_name": "My Application",
        "license": "GPL-2.0",
        "module_name": "myapplication",
        "source_dir": "src/myapplication",
        "test_source_dir": "tests",
        "project_name": "My Project",
        "url": "https://navy.mil/myapplication",
    }


def test_question_sequence_with_overrides(new_command):
    """Overrides can be used to set the answers for questions."""

    # Prime answers for none of the questions.
    new_command.console.values = []

    context = new_command.build_app_context(
        project_overrides={
            "formal_name": "My Override App",
            "app_name": "myoverrideapp",
            "bundle": "net.example",
            "project_name": "My Override Project",
            "description": "My override description",
            "author": "override, author",
            "author_email": "author@override.tld",
            "url": "https://override.example.com",
            "license": "MIT",
        },
    )

    assert context == {
        "app_name": "myoverrideapp",
        "author": "override, author",
        "author_email": "author@override.tld",
        "bundle": "net.example",
        "class_name": "MyOverrideApp",
        "description": "My override description",
        "formal_name": "My Override App",
        "license": "MIT",
        "module_name": "myoverrideapp",
        "source_dir": "src/myoverrideapp",
        "test_source_dir": "tests",
        "project_name": "My Override Project",
        "url": "https://override.example.com",
    }


def test_question_sequence_with_bad_license_override(new_command):
    """A bad override for license uses user input instead."""

    # Prime answers for all the questions.
    new_command.console.values = [
        "4",  # license
    ]

    context = new_command.build_app_context(
        project_overrides={
            "formal_name": "My Override App",
            "app_name": "myoverrideapp",
            "bundle": "net.example",
            "project_name": "My Override Project",
            "description": "My override description",
            "author": "override, author",
            "author_email": "author@override.tld",
            "url": "https://override.example.com",
            "license": "BAD i don't exist license",
        },
    )

    assert context == {
        "app_name": "myoverrideapp",
        "author": "override, author",
        "author_email": "author@override.tld",
        "bundle": "net.example",
        "class_name": "MyOverrideApp",
        "description": "My override description",
        "formal_name": "My Override App",
        "license": "GPL-2.0",
        "module_name": "myoverrideapp",
        "source_dir": "src/myoverrideapp",
        "test_source_dir": "tests",
        "project_name": "My Override Project",
        "url": "https://override.example.com",
    }


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.console.input_enabled = False

    context = new_command.build_app_context(project_overrides={})

    assert context == {
        "app_name": "helloworld",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
        "bundle": "com.example",
        "class_name": "HelloWorld",
        "description": "My first application",
        "formal_name": "Hello World",
        "license": "BSD-3-Clause",
        "module_name": "helloworld",
        "source_dir": "src/helloworld",
        "test_source_dir": "tests",
        "project_name": "Hello World",
        "url": "https://example.com/helloworld",
    }


def test_author_and_email_use_git_config_as_fallback(new_command):
    """If no user input is provided, git config values 'git.user' and 'git.email' are used if
    available."""
    new_command.tools.git = object()
    new_command.get_git_config_value = mock.MagicMock()
    new_command.get_git_config_value.side_effect = ["Some Author", "my@email.com"]

    new_command.console.input_enabled = False

    context = new_command.build_app_context(project_overrides={})

    assert context["author"] == "Some Author"
    assert context["author_email"] == "my@email.com"
    assert new_command.get_git_config_value.call_args_list == [
        mock.call("user", "name"),
        mock.call("user", "email"),
    ]


def test_git_config_is_mentioned_as_source(new_command, monkeypatch):
    """If git config is used as default value, this shall be mentioned to the user."""
    new_command.tools.git = object()
    new_command.get_git_config_value = mock.MagicMock()
    new_command.get_git_config_value.side_effect = ["Some Author", "my@email.com"]

    new_command.console.input_enabled = False

    mock_text_question = mock.MagicMock()
    mock_text_question.side_effect = lambda *args, **kwargs: kwargs["default"]
    monkeypatch.setattr(new_command.console, "text_question", mock_text_question)

    new_command.build_app_context(project_overrides={})

    assert (
        mock.call(
            intro=PartialMatchString("Based on your git configuration"),
            description="Author",
            default="Some Author",
            override_value=None,
        )
        in mock_text_question.call_args_list
    )

    assert (
        mock.call(
            intro=PartialMatchString("Based on your git configuration"),
            description="Author's Email",
            default="my@email.com",
            override_value=None,
            validator=new_command.validate_email,
        )
        in mock_text_question.call_args_list
    )
