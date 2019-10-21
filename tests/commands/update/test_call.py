
def test_update(update_command, tmp_path, first_app, second_app):
    "The update command can be called"

    update_command(path=tmp_path)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('dependencies', update_command.apps['first'], tmp_path),
        ('code', update_command.apps['first'], tmp_path),

        # Update the second app
        ('dependencies', update_command.apps['second'], tmp_path),
        ('code', update_command.apps['second'], tmp_path),
    ]


def test_update_single(update_command, tmp_path, first_app, second_app):
    "The update command can be called to update a single app from the config"

    update_command(app=update_command.apps['first'], path=tmp_path)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # update the first app
        ('dependencies', update_command.apps['first'], tmp_path),
        ('code', update_command.apps['first'], tmp_path),
    ]
