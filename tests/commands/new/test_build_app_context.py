from unittest import mock


def test_question_sequence(new_command):
    "Questions are asked, a context is constructed."

    # Prime answers for all the questions.
    new_command.input = mock.MagicMock(side_effect=[
        'My Application',  # formal name
        '',  # app name - accept the default
        'org.beeware',  # bundle ID
        'My Project',  # project name
        'Cool stuff',  # description
        'Grace Hopper',  # author
        'grace@navy.mil',  # author email
        'https://navy.mil/myapplication',  # URL
        '4',  # license
        '1',  # GUI toolkit
    ])

    assert new_command.build_app_context() == {
        'formal_name': 'My Application',
        'class_name': 'MyApplication',
        'app_name': 'myapplication',
        'module_name': 'myapplication',
        'bundle': 'org.beeware',
        'class_name': 'MyApplication',
        'project_name': 'My Project',
        'description': 'Cool stuff',
        'author': 'Grace Hopper',
        'author_email': 'grace@navy.mil',
        'url': 'https://navy.mil/myapplication',
        'license': 'GNU General Public License v2 (GPLv2)',
        'gui_framework': 'Toga',
    }
