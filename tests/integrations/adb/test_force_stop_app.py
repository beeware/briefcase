from unittest.mock import MagicMock

from briefcase.integrations.adb import ADB


def test_force_stop_app(tmp_path, capsys):
    "Invoking `force_stop_app()` calls `run()` with the appropriate parameters."
    # Mock out the run command on an adb instance
    adb = ADB(tmp_path, "exampleDevice")
    adb.command = MagicMock(return_value=b"example normal adb output")

    # Invoke force_stop_app
    adb.force_stop_app("com.example.sample.package")

    # Validate call parameters.
    adb.command.assert_called_once_with(
        "shell", "am", "force-stop", "com.example.sample.package"
    )

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()
