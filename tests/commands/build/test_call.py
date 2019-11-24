import argparse


def test_specific_app(build_command, first_app, second_app):
    "If a specific app is requested, build it"
    # Add two apps
    build_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, [])

    # Run the build command
    build_command(first_app, **options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Build the first app
        ('build', 'first'),
    ]


def test_multiple_apps(build_command, first_app, second_app):
    "If there are multiple apps, build all of them"
    # Add two apps
    build_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, [])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Build the first app
        ('build', 'first'),

        # Build the second app
        ('build', 'second'),
    ]


def test_non_existent(build_command, first_app_config, second_app):
    "Requesting a build of a non-existent app causes a create"
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        'first': first_app_config,
        'second': second_app,
    }

    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, [])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App doesn't exist, so it will be created, then built
        ('create', 'first'),
        ('build', 'first'),

        # Second app *does* exist, so it only be built
        ('build', 'second'),
    ]


def test_unbuilt(build_command, first_app_unbuilt, second_app):
    "Requesting a build of an app that has been created, but not build, just causes a build"
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        'first': first_app_unbuilt,
        'second': second_app,
    }

    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, [])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App exists, but hasn't been built; it will be built.
        ('build', 'first'),

        # Second app has been built before; it will be built again.
        ('build', 'second'),
    ]


def test_update_app(build_command, first_app, second_app):
    "If an update is requested, app is updated before build"
    # Add two apps
    build_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a -a command line option
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, ['-u'])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Update then build the first app
        ('update', 'first'),
        ('build', 'first'),

        # Update then build the second app
        ('update', 'second'),
        ('build', 'second'),
    ]


def test_update_non_existent(build_command, first_app_config, second_app):
    "Requesting an update of a non-existent app causes a create"
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        'first': first_app_config,
        'second': second_app,
    }

    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, ['-u'])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App doesn't exist, so it will be created, then built
        ('create', 'first'),
        ('build', 'first'),

        # Second app *does* exist, so it will be updated, then built
        ('update', 'second'),
        ('build', 'second'),
    ]


def test_update_unbuilt(build_command, first_app_unbuilt, second_app):
    "Requesting an update of an upbuilt app causes an update before build"
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        'first': first_app_unbuilt,
        'second': second_app,
    }

    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    options = build_command.parse_options(parser, ['-u'])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App exists, but hasn't been built; it will updated then built.
        ('update', 'first'),
        ('build', 'first'),

        # Second app has been built before; it will be built again.
        ('update', 'second'),
        ('build', 'second'),
    ]
