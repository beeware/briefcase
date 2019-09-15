from .base import BaseCommand


class BuildCommand(BaseCommand):
    def __call__(self):
        print("BUILD:", self.description)

    # requires create
    # causes update on flag
