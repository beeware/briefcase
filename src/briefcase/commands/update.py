from .base import BaseCommand


class UpdateCommand(BaseCommand):
    def __call__(self):
        print("UPDATE:", self.description)

    # requires create
