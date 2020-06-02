import pytest


@pytest.fixture
def defaults():
    """Default dictionary reflecting briefcase-template cookiecutter.json"""
    defaults = {
        "formal_name": "Hello World",
        "app_name": "helloworld",
        "class_name": "HelloWorld",
        "module_name": "helloworld",
        "project_name": "Project Awesome",
        "description": "An app that does lots of stuff",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
        "bundle": "com.example",
        "url": "https://example.com",
        "license": [
            "BSD license",
            "MIT license",
            "Apache Software License",
            "GNU General Public License v2 (GPLv2)",
            "GNU General Public License v2 or later (GPLv2+)",
            "GNU General Public License v3 (GPLv3)",
            "GNU General Public License v3 or later (GPLv3+)",
            "Proprietary",
            "Other",
        ],
        "gui_framework": ["Toga", "PySide2", "PursuedPyBear", "None"],
    }
    return defaults


def test_question_sequence(new_command, defaults):
    "Questions are asked, a context is constructed."

    # Prime answers for all the questions.
    new_command.input.values = [
        'My Application',  # formal name
        '',  # app name - accept the default
        '',  # class name - accept the default
        '',  # module name - accept the default
        'My Project',  # project name
        'Cool stuff',  # description
        'Grace Hopper',  # author
        'grace@navy.mil',  # author email
        'org.beeware',  # bundle ID
        'https://navy.mil/myapplication',  # URL
        '4',  # license
        '1',  # GUI toolkit
    ]

    assert new_command.build_app_context(defaults) == {
        'formal_name': 'My Application',
        'app_name': 'myapplication',
        'class_name': 'MyApplication',
        'module_name': 'myapplication',
        'project_name': 'My Project',
        'description': 'Cool stuff',
        'author': 'Grace Hopper',
        'author_email': 'grace@navy.mil',
        'bundle': 'org.beeware',
        'url': 'https://navy.mil/myapplication',
        'license': 'GNU General Public License v2 (GPLv2)',
        'gui_framework': 'Toga',
    }


def test_question_sequence_with_no_user_input(new_command, defaults):
    "If no user input is provided, all user inputs are taken as default"

    new_command.input.enabled = False

    assert new_command.build_app_context(defaults) == {
        'formal_name': 'Hello World',
        'app_name': 'helloworld',
        'class_name': 'HelloWorld',
        'module_name': 'helloworld',
        'project_name': 'Project Awesome',
        'description': 'An app that does lots of stuff',
        'author': 'Jane Developer',
        'author_email': 'jane@example.com',
        'bundle': 'com.example',
        'url': 'https://example.com',
        'license': 'BSD license',
        'gui_framework': 'Toga',
    }
