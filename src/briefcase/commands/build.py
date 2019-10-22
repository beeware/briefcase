from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand


class BuildCommand(BaseCommand):
    def __call__(self, app: Optional[BaseConfig] = None):
        print("BUILD:", self.description)

        # requires create
        # causes update on flag
