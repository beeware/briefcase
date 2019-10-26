import argparse


def test_update(update_command, first_app, second_app):
    "The update command can be called"
    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    update_command.parse_options(parser, [])

    update_command()

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('code', update_command.apps['first']),

        # Update the second app
        ('code', update_command.apps['second']),
    ]


def test_update_single(update_command, first_app, second_app):
    "The update command can be called to update a single app from the config"
    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    update_command.parse_options(parser, [])

    update_command(app=update_command.apps['first'])

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # update the first app
        ('code', update_command.apps['first']),
    ]


def test_update_with_dependencies(update_command, first_app, second_app):
    "The update command can be called"
    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    update_command.parse_options(parser, ['-d'])

    update_command()

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('dependencies', update_command.apps['first']),
        ('code', update_command.apps['first']),

        # Update the second app
        ('dependencies', update_command.apps['second']),
        ('code', update_command.apps['second']),
    ]


def test_update_with_extras(update_command, first_app, second_app):
    "The update command can be called"
    # Configure no command line options
    parser = argparse.ArgumentParser(prog='briefcase')
    update_command.parse_options(parser, ['-e'])

    update_command()

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('code', update_command.apps['first']),
        ('extras', update_command.apps['first']),

        # Update the second app
        ('code', update_command.apps['second']),
        ('extras', update_command.apps['second']),
    ]
