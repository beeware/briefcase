def test_project_command(project_command, capsys):
    project_command(app=project_command.apps["first"])
    assert capsys.readouterr().out == "project.version=0.0.1\n"
