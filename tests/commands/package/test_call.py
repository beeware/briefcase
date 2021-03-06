

def test_no_args_package_one_app(package_command, first_app):
    "If there is one app, package that app by default"
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                'adhoc_sign': False,
                'identity': None,
                'sign_app': True,
            }
        ),
    ]


def test_no_args_package_two_app(package_command, first_app, second_app):
    "If there are multiple apps, publish all of them"
    # Add two apps
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = package_command.parse_options([])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                'adhoc_sign': False,
                'identity': None,
                'sign_app': True,
            }
        ),
        # package the second app
        (
            "package",
            "second",
            {
                'packaging_format': 'pkg',
                "adhoc_sign": False,
                "identity": None,
                "sign_app": True,
                "package_state": "first",
            },
        ),
    ]


def test_no_sign_package_one_app(package_command, first_app):
    "If there is one app, and a --no-sign argument,package doesnt sign the app"
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = package_command.parse_options(["--no-sign"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                'adhoc_sign': False,
                'identity': None,
                'sign_app': False,
            }
        ),
    ]


def test_identity_arg_package_one_app(package_command, first_app):
    "If there is one app,and an --identity argument, package signs the app with the specified identity"
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = package_command.parse_options(["--identity", "test"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                "adhoc_sign": False,
                "identity": "test",
                "sign_app": True,
            },
        ),
    ]


def test_adhoc_sign_package_one_app(package_command, first_app):
    "If there is one app,and an --adhoc argument, package signs the app using adhoc option"
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = package_command.parse_options(["--adhoc"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                'adhoc_sign': True,
                'identity': None,
                'sign_app': True,
            }
        ),
    ]


def test_no_sign_args_package_two_app(package_command, first_app, second_app):
    "If there are multiple apps, and a --no-sign argument,package doesnt sign all the app"
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = package_command.parse_options(["--no-sign"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                'adhoc_sign': False,
                'identity': None,
                'sign_app': False,
            }
        ),
        # package the second app
        (
            "package",
            "second",
            {
                'packaging_format': 'pkg',
                "adhoc_sign": False,
                "identity": None,
                "sign_app": False,
                "package_state": "first",
            },
        ),
    ]


def test_adhoc_sign_args_package_two_app(package_command, first_app, second_app):
    "If there are multiple apps,and an --adhoc argument, package signs all apps using adhoc option"

    package_command.apps = {
        # Add the first app
        "first": first_app,
        # Add the second app
        "second": second_app,
    }

    # Configure adhoc command line options
    options = package_command.parse_options(["--adhoc"])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                'adhoc_sign': True,
                'identity': None,
                'sign_app': True,
            }
        ),
        # package the second app
        (
            "package",
            "second",
            {
                'packaging_format': 'pkg',
                "adhoc_sign": True,
                "identity": None,
                "sign_app": True,
                "package_state": "first",
            },
        ),
    ]


def test_identity_sign_args_package_two_app(package_command, first_app, second_app):
    "If there are multiple app,and an --identity argument, package signs all the apps with the specified identity"
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = package_command.parse_options(["--identity", "test"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'pkg',
                "adhoc_sign": False,
                "identity": "test",
                "sign_app": True,
            },
        ),
        # package the second app
        (
            "package",
            "second",
            {
                'packaging_format': 'pkg',
                "adhoc_sign": False,
                "identity": "test",
                "sign_app": True,
                "package_state": "first",
            },
        ),
    ]


def test_package_alternate_format(package_command, first_app):
    "An app can be packaged in an alternate format"
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure command line options with an alternate format
    options = package_command.parse_options(['--packaging-format', 'box'])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Tools are verified
        ("verify", ),
        # Package the first app
        (
            "package",
            "first",
            {
                'packaging_format': 'box',
                'adhoc_sign': False,
                'identity': None,
                'sign_app': True,
            }
        ),
    ]
