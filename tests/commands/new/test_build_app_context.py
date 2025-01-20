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

    assert context == dict(
        app_name="myapplication",
        author="Grace Hopper",
        author_email="grace@navy.mil",
        bundle="org.beeware",
        class_name="MyApplication",
        description="Cool stuff",
        formal_name="My Application",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myapplication",
        source_dir="src/myapplication",
        test_source_dir="tests",
        project_name="My Project",
        url="https://navy.mil/myapplication",
    )


def test_question_sequence_with_overrides(new_command):
    """Overrides can be used to set the answers for questions."""

    # Prime answers for none of the questions.
    new_command.console.values = []

    context = new_command.build_app_context(
        project_overrides=dict(
            formal_name="My Override App",
            app_name="myoverrideapp",
            bundle="net.example",
            project_name="My Override Project",
            description="My override description",
            author="override, author",
            author_email="author@override.tld",
            url="https://override.example.com",
            license="MIT license",
        ),
    )

    assert context == dict(
        app_name="myoverrideapp",
        author="override, author",
        author_email="author@override.tld",
        bundle="net.example",
        class_name="MyOverrideApp",
        description="My override description",
        formal_name="My Override App",
        license="MIT license",
        module_name="myoverrideapp",
        source_dir="src/myoverrideapp",
        test_source_dir="tests",
        project_name="My Override Project",
        url="https://override.example.com",
    )


def test_question_sequence_with_bad_license_override(new_command):
    """A bad override for license uses user input instead."""

    # Prime answers for all the questions.
    new_command.console.values = [
        "4",  # license
    ]

    context = new_command.build_app_context(
        project_overrides=dict(
            formal_name="My Override App",
            app_name="myoverrideapp",
            bundle="net.example",
            project_name="My Override Project",
            description="My override description",
            author="override, author",
            author_email="author@override.tld",
            url="https://override.example.com",
            license="BAD i don't exist license",
        ),
    )

    assert context == dict(
        app_name="myoverrideapp",
        author="override, author",
        author_email="author@override.tld",
        bundle="net.example",
        class_name="MyOverrideApp",
        description="My override description",
        formal_name="My Override App",
        license="GNU General Public License v2 (GPLv2)",
        module_name="myoverrideapp",
        source_dir="src/myoverrideapp",
        test_source_dir="tests",
        project_name="My Override Project",
        url="https://override.example.com",
    )


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.console.input_enabled = False

    context = new_command.build_app_context(project_overrides={})

    assert context == dict(
        app_name="helloworld",
        author="Jane Developer",
        author_email="jane@example.com",
        bundle="com.example",
        class_name="HelloWorld",
        description="My first application",
        formal_name="Hello World",
        license="BSD license",
        module_name="helloworld",
        source_dir="src/helloworld",
        test_source_dir="tests",
        project_name="Hello World",
        url="https://example.com/helloworld",
    )
