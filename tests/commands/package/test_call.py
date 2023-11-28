from ...utils import create_file


def test_no_args_package_one_app(package_command, first_app, tmp_path):
    """If there is one app, package that app by default."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options, _ = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_package_one_explicit_app(package_command, first_app, second_app, tmp_path):
    """If one app is named explicitly, package that app."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line arguments
    options, _ = package_command.parse_options([])

    # Run the build command on a specific app
    package_command(first_app, **options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
    ]

    # Packaging format has been annotated on the first app, not the second.
    assert first_app.packaging_format == "pkg"
    assert not hasattr(second_app, "packaging_format")

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_no_args_package_two_app(package_command, first_app, second_app, tmp_path):
    """If there are multiple apps, publish all of them."""
    # Add two apps
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = package_command.parse_options([])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "adhoc_sign": False,
                "identity": None,
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on both apps
    assert first_app.packaging_format == "pkg"
    assert second_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_identity_arg_package_one_app(package_command, first_app, tmp_path):
    """If there is one app,and an --identity argument, package signs the app with the
    specified identity."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure an identity option
    options, _ = package_command.parse_options(["--identity", "test"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": "test",
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_adhoc_sign_package_one_app(package_command, first_app, tmp_path):
    """If there is one app,and an --adhoc argument, package signs the app using ad-hoc
    option."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure an ad-hoc signing option
    options, _ = package_command.parse_options(["--adhoc-sign"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": True,
                "identity": None,
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_adhoc_sign_args_package_two_app(
    package_command, first_app, second_app, tmp_path
):
    """If there are multiple apps,and an --adhoc argument, package signs all apps using
    ad-hoc identity."""

    package_command.apps = {
        # Add the first app
        "first": first_app,
        # Add the second app
        "second": second_app,
    }

    # Configure adhoc command line options
    options, _ = package_command.parse_options(["--adhoc-sign"])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": True,
                "identity": None,
            },
        ),
        # App template is verified
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "adhoc_sign": True,
                "identity": None,
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on both apps
    assert first_app.packaging_format == "pkg"
    assert second_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_identity_sign_args_package_two_app(
    package_command, first_app, second_app, tmp_path
):
    """If there are multiple app,and an --identity argument, package signs all the apps
    with the specified identity."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure an identity option
    options, _ = package_command.parse_options(["--identity", "test"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": "test",
            },
        ),
        # App template is verified
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "adhoc_sign": False,
                "identity": "test",
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on both apps
    assert first_app.packaging_format == "pkg"
    assert second_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_package_alternate_format(package_command, first_app, tmp_path):
    """An app can be packaged in an alternate format."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure command line options with an alternate format
    options, _ = package_command.parse_options(["--packaging-format", "box"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app.packaging_format == "box"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_create_before_package(package_command, first_app_config, tmp_path):
    """If the app hasn't been created, package creates the app first."""
    # Add a single app
    package_command.apps = {
        "first": first_app_config,
    }

    # Configure no command line options
    options, _ = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # Create and then build the first app
        (
            "create",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "create_state": "first",
                "identity": None,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "create_state": "first",
                "build_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app_config.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_update_package_one_app(package_command, first_app, tmp_path):
    """If there is one app, and a -u argument, package updates the app."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Configure an update option
    options, _ = package_command.parse_options(["-u"])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # Update (and then build) the first app
        (
            "update",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_requirements": True,
                "update_resources": True,
                "update_support": True,
            },
        ),
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_state": "first",
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_state": "first",
                "build_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_update_package_two_app(package_command, first_app, second_app, tmp_path):
    """If there are multiple apps, update and publish all of them."""
    # Add two apps
    package_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure an update option
    options, _ = package_command.parse_options(["--update"])

    # Run the package command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update (and then build) the first app
        (
            "update",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_requirements": True,
                "update_resources": True,
                "update_support": True,
            },
        ),
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_state": "first",
            },
        ),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_state": "first",
                "build_state": "first",
            },
        ),
        # Update (and then build) the second app
        (
            "update",
            "second",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_requirements": True,
                "update_resources": True,
                "update_support": True,
                # state of previous calls have been preserved.
                "update_state": "first",
                "build_state": "first",
                "package_state": "first",
            },
        ),
        (
            "build",
            "second",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_state": "second",
                # state of previous calls have been preserved.
                "build_state": "first",
                "package_state": "first",
            },
        ),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # package the second app
        (
            "package",
            "second",
            {
                "adhoc_sign": False,
                "identity": None,
                "update_state": "second",
                "build_state": "second",
                # state of previous calls have been preserved.
                "package_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on both apps
    assert first_app.packaging_format == "pkg"
    assert second_app.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_build_before_package(package_command, first_app_unbuilt, tmp_path):
    """If an app hasn't been built, it is built before packaging."""
    # Add a single app
    package_command.apps = {
        "first": first_app_unbuilt,
    }

    # Configure no command line options
    options, _ = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # Build the first app
        (
            "build",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
                "build_state": "first",
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app_unbuilt.packaging_format == "pkg"

    # The dist folder has been created.
    assert tmp_path / "base_path/dist"


def test_already_packaged(package_command, first_app, tmp_path):
    """If the app has been previously packaged, the old version is deleted."""
    # Add a single app
    package_command.apps = {
        "first": first_app,
    }

    # Mock a historical package artefact.
    artefact_path = tmp_path / "base_path/dist/first-0.0.1.pkg"
    create_file(artefact_path, "Packaged app")

    # Configure no command line options
    options, _ = package_command.parse_options([])

    # Run the run command
    package_command(**options)

    # The right sequence of things will be done
    assert package_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Package the first app
        (
            "package",
            "first",
            {
                "adhoc_sign": False,
                "identity": None,
            },
        ),
    ]

    # Packaging format has been annotated on the app
    assert first_app.packaging_format == "pkg"

    # The dist folder still exists
    assert tmp_path / "base_path/dist"

    # But the artefact has been deleted.
    # NOTE: This is a testing quirk - because we're mocking the
    # package_app() call, no new artefact is created; the absence
    # of this file shows that the old one has been deleted.
    assert not artefact_path.exists()
