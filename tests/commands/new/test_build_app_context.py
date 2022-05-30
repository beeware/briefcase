def test_question_sequence(new_command):
    """Questions are asked, a context is constructed."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "1",  # GUI toolkit
    ]

    assert new_command.build_app_context() == {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "myapplication",
        "bundle": "org.beeware",
        "project_name": "My Project",
        "description": "Cool stuff",
        "author": "Grace Hopper",
        "author_email": "grace@navy.mil",
        "url": "https://navy.mil/myapplication",
        "license": "GNU General Public License v2 (GPLv2)",
        "gui_framework": "Toga",
    }


def test_question_sequence_with_nondefault_gui(new_command):
    """Questions are asked, a context is constructed, but the GUI option is
    formatted to extract the GUI name."""

    # Prime answers for all the questions.
    new_command.input.values = [
        "My Application",  # formal name
        "",  # app name - accept the default
        "org.beeware",  # bundle ID
        "My Project",  # project name
        "Cool stuff",  # description
        "Grace Hopper",  # author
        "grace@navy.mil",  # author email
        "https://navy.mil/myapplication",  # URL
        "4",  # license
        "2",  # GUI toolkit
    ]

    assert new_command.build_app_context() == {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "myapplication",
        "bundle": "org.beeware",
        "project_name": "My Project",
        "description": "Cool stuff",
        "author": "Grace Hopper",
        "author_email": "grace@navy.mil",
        "url": "https://navy.mil/myapplication",
        "license": "GNU General Public License v2 (GPLv2)",
        "gui_framework": "PySide2",
    }


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.input.enabled = False

    assert new_command.build_app_context() == {
        "app_name": "helloworld",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
        "bundle": "com.example",
        "class_name": "HelloWorld",
        "description": "My first application",
        "formal_name": "Hello World",
        "gui_framework": "Toga",
        "license": "BSD license",
        "module_name": "helloworld",
        "project_name": "Hello World",
        "url": "https://example.com/helloworld",
    }
