def test_update_app(update_command, first_app, tmp_path):
    """If the app already exists, it will be updated."""
    update_command.update_app(
        update_command.apps["first"],
        update_requirements=False,
        update_resources=False,
        update_support=False,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("cleanup", "first"),
    ]

    # App content and resources have been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    # requirements and resources haven't been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    assert not (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()


def test_update_non_existing_app(update_command, tmp_path):
    """If the app hasn't been generated yet, it won't be created."""

    update_command.update_app(
        update_command.apps["first"],
        update_requirements=False,
        update_resources=False,
        update_support=False,
        test_mode=False,
    )

    # No app creation actions will be performed
    assert update_command.actions == []

    # App content has been not updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    assert not (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()


def test_update_app_with_requirements(update_command, first_app, tmp_path):
    """If the user requests a dependency update, they are updated."""
    update_command.update_app(
        update_command.apps["first"],
        update_requirements=True,
        update_resources=False,
        update_support=False,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("cleanup", "first"),
    ]

    # App content has been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    # Extras haven't been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()


def test_update_app_with_resources(update_command, first_app, tmp_path):
    """If the user requests a resources update, they are updated."""
    update_command.update_app(
        update_command.apps["first"],
        update_requirements=False,
        update_resources=True,
        update_support=False,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
    ]

    # App content and resources have been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    assert (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    # requirements haven't been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()


def test_update_app_with_support_package(update_command, first_app, tmp_path):
    """If the user requests an app support package update, they are updated."""
    update_command.update_app(
        update_command.apps["first"],
        update_requirements=False,
        update_resources=False,
        update_support=True,
        test_mode=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("cleanup-support", "first"),
        ("support", "first"),
        ("cleanup", "first"),
    ]

    # App content and support have been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    assert (tmp_path / "base_path/build/first/tester/dummy/support").exists()
    # requirements and resources haven't been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    assert not (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()


def test_update_app_test_mode(update_command, first_app, tmp_path):
    """Update app in test mode."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update_requirements=False,
        update_resources=False,
        update_support=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", True),
        ("cleanup", "first"),
    ]

    # App code has been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    # App requirements and resources have not been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    assert not (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()


def test_update_app_test_mode_requirements(update_command, first_app, tmp_path):
    """Update app in test mode, but with requirements."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update_requirements=True,
        update_resources=False,
        update_support=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", True),
        ("requirements", "first", True),
        ("cleanup", "first"),
    ]

    # App content and requirements have been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    assert (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    # App resources have not been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()


def test_update_app_test_mode_resources(update_command, first_app, tmp_path):
    """Update app in test mode, but with resources."""
    # Pass in the defaults for the update flags
    update_command.update_app(
        update_command.apps["first"],
        test_mode=True,
        update_requirements=False,
        update_resources=True,
        update_support=False,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", True),
        ("resources", "first"),
        ("cleanup", "first"),
    ]

    # App content and resources have been updated
    assert (tmp_path / "base_path/build/first/tester/dummy/code.py").exists()
    assert (tmp_path / "base_path/build/first/tester/dummy/resources").exists()
    # App requirements have not been updated
    assert not (tmp_path / "base_path/build/first/tester/dummy/requirements").exists()
    # ... and the app still exists
    assert (tmp_path / "base_path/build/first/tester/dummy/first.bundle").exists()
