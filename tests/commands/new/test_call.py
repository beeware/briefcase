
def test_new_app(new_command):
    "A new application can be created."

    # Configure no command line options
    options = new_command.parse_options([])

    # Run the run command
    new_command(**options)

    # The right sequence of things will be done
    assert new_command.actions == [
        # Run the first app
        ('new', {'template': None, 'verbosity': 1}),
    ]
