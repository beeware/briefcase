from unittest.mock import MagicMock

import briefcase.console
from briefcase.console import NotDeadYet, Printer


def test_update(capsys, monkeypatch):
    """The message is only printed once for each interval."""
    # initialization will set interval to 0 + 10
    # update() will see time either at 5 or 15 and print the message accordingly
    # then interval is reset back to 0 + 10
    monkeypatch.setattr(
        briefcase.console.time,
        "time",
        MagicMock(side_effect=[0] + [10 - 5, 10 + 5, 0] * 3),
    )

    keep_alive = NotDeadYet(printer=Printer())

    for _ in range(3):
        keep_alive.update()
        keep_alive.update()

    assert capsys.readouterr().out == (
        "... still waiting\n... still waiting\n... still waiting\n"
    )


def test_reset(capsys, monkeypatch):
    """Calling reset always puts the interval in the future and nothing prints."""
    # initialization will set interval to 0 + 10
    # the reset updates the interval to 10 + 10
    # the update sees a time of 15 and doesn't print or reset
    monkeypatch.setattr(
        briefcase.console.time,
        "time",
        MagicMock(side_effect=[0] + [10, 15] * 10),
    )

    keep_alive = NotDeadYet(printer=Printer())

    for _ in range(10):
        keep_alive.reset()
        keep_alive.update()

    assert capsys.readouterr().out == ""
