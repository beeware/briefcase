from .base import BaseCommand


class PublishCommand(BaseCommand):
    # requires build
    # causes update && build on flag

    def __call__(self):
        print("PUBLISH:", self.description)
