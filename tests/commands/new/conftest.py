import pytest

from briefcase.commands import NewCommand
from briefcase.commands.base import full_kwargs


class DummyNewCommand(NewCommand):
    """
    A dummy new command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """
    description = 'Dummy new command'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps=[], **kwargs)

        self.actions = []

    def new_app(self, **kwargs):
        self.actions.append(('new', kwargs))
        return full_kwargs({
            'new_state': 'done'
        }, kwargs)


@pytest.fixture
def new_command(tmp_path):
    return DummyNewCommand(base_path=tmp_path)
