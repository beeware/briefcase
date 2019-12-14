
from .base import BaseCommand


class NewCommand(BaseCommand):
    cmd_line = 'briefcase new'
    command = 'new'
    platform = 'all'
    output_format = None
    description = 'Create a new briefcase project'

    def bundle_path(self, app):
        "A placeholder; New command doesn't have a bundle path"
        raise NotImplementedError()

    def binary_path(self, app):
        "A placeholder; New command doesn't have a binary path"
        raise NotImplementedError()

    def distribution_path(self, app):
        "A placeholder; New command doesn't have a distribution path"
        raise NotImplementedError()

    def new_app(self, **kwargs):
        raise NotImplementedError()

    def __call__(
        self,
        **kwargs
    ):
        state = self.new_app(**kwargs)
        return state
