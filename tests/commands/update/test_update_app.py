def test_update_app(update_command, first_app):
    """If the app already exists, it will be updated."""
    update_command.update_app(
        update_command.apps["first"],
        update=True,
        update_requirements=False,
        update_resources=False,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("code", update_command.apps["first"], False),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content and resources have been updated
    assert (update_command.platform_path / "first.dummy" / "code.py").exists()
    # requirements and resources haven't been updated
    assert not (update_command.platform_path / "first.dummy" / "requirements").exists()
    assert not (update_command.platform_path / "first.dummy" / "resources").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_non_existing_app(update_command):
    """If the app hasn't been generated yet, it won't be created."""

    update_command.update_app(
        update_command.apps["first"],
        update=True,
        update_requirements=False,
        update_resources=False,
        test_mode=False,
    )

    # No app creation actions will be performed
    assert update_command.actions == []

    # App content has been not updated
    assert not (update_command.platform_path / "first.dummy" / "requirements").exists()
    assert not (update_command.platform_path / "first.dummy" / "code.py").exists()


def test_update_app_with_requirements(update_command, first_app):
    """If the user requests a dependency update, they are updated."""
    update_command.update_app(
        update_command.apps["first"],
        update=True,
        update_requirements=True,
        update_resources=False,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("code", update_command.apps["first"], False),
        ("requirements", update_command.apps["first"], False),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content has been updated
    assert (update_command.platform_path / "first.dummy" / "requirements").exists()
    assert (update_command.platform_path / "first.dummy" / "code.py").exists()
    # Extras haven't been updated
    assert not (update_command.platform_path / "first.dummy" / "resources").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_app_with_resources(update_command, first_app):
    """If the user requests a resources update, they are updated."""
    update_command.update_app(
        update_command.apps["first"],
        update=True,
        update_requirements=False,
        update_resources=True,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("code", update_command.apps["first"], False),
        ("resources", update_command.apps["first"]),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content and resources have been updated
    assert (update_command.platform_path / "first.dummy" / "code.py").exists()
    assert (update_command.platform_path / "first.dummy" / "resources").exists()
    # requirements haven't been updated
    assert not (update_command.platform_path / "first.dummy" / "requirements").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_app_no_op(update_command, first_app):
    """Programmatically, it is possible to update an app and *not* update
    code."""
    # Pass in an explicit "no update". This can't happen from the
    # `update` command line, but it can happen as a call from other commands.
    update_command.update_app(
        update_command.apps["first"],
        update=False,
        update_requirements=False,
        update_resources=False,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("cleanup", update_command.apps["first"]),
    ]

    # App content, requirements or resources have not been updated
    assert not (update_command.platform_path / "first.dummy" / "code.py").exists()
    assert not (update_command.platform_path / "first.dummy" / "requirements").exists()
    assert not (update_command.platform_path / "first.dummy" / "resources").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_app_test_mode(update_command, first_app):
    """Update app in test mode."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update=None,
        update_requirements=None,
        update_resources=None,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("code", update_command.apps["first"], True),
        ("requirements", update_command.apps["first"], True),
        ("resources", update_command.apps["first"]),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content, requirements and resources have been updated
    assert (update_command.platform_path / "first.dummy" / "code.py").exists()
    assert (update_command.platform_path / "first.dummy" / "requirements").exists()
    assert (update_command.platform_path / "first.dummy" / "resources").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_app_test_mode_no_update(update_command, first_app):
    """Update app in test mode, but disable app update."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update=False,
        update_requirements=None,
        update_resources=None,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("requirements", update_command.apps["first"], True),
        ("resources", update_command.apps["first"]),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content has not been updated
    assert not (update_command.platform_path / "first.dummy" / "code.py").exists()
    # App requirements and resources have been updated
    assert (update_command.platform_path / "first.dummy" / "requirements").exists()
    assert (update_command.platform_path / "first.dummy" / "resources").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_app_test_mode_no_requirements(update_command, first_app):
    """Update app in test mode, but without requirements."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update=None,
        update_requirements=False,
        update_resources=None,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("code", update_command.apps["first"], True),
        ("resources", update_command.apps["first"]),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content and resources have been updated
    assert (update_command.platform_path / "first.dummy" / "code.py").exists()
    assert (update_command.platform_path / "first.dummy" / "resources").exists()
    # App requirements have not been updated
    assert not (update_command.platform_path / "first.dummy" / "requirements").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()


def test_update_app_test_mode_no_resources(update_command, first_app):
    """Update app in test mode, but disable resources update."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update=None,
        update_requirements=None,
        update_resources=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("code", update_command.apps["first"], True),
        ("requirements", update_command.apps["first"], True),
        ("cleanup", update_command.apps["first"]),
    ]

    # App content and requirements have been updated
    assert (update_command.platform_path / "first.dummy" / "code.py").exists()
    assert (update_command.platform_path / "first.dummy" / "requirements").exists()
    # App resources have not been updated
    assert not (update_command.platform_path / "first.dummy" / "resources").exists()
    # ... and the app still exists
    assert (update_command.platform_path / "first.dummy" / "Content").exists()
