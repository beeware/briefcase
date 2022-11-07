from abc import abstractmethod
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import NativeAppContext

from .base import BaseCommand, full_options


class MissingTestSources(BriefcaseCommandError):
    def __init__(self, src):
        self.src = src
        super().__init__(f"Application test source {src!r} does not exist.")


class TestCommand(BaseCommand):
    command = "test"

    def add_options(self, parser):
        parser.add_argument("-a", "--app", dest="appname", help="The app to run")
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="Update the app before execution",
        )

    @abstractmethod
    def test_app(self, app: BaseConfig, **options):
        """Test an application.

        :param app: The application to test
        """
        ...

    def verify_app_tools(self, app: BaseConfig):
        """Verify that tools needed to run the command for this app exist."""
        super().verify_app_tools(app)
        NativeAppContext.verify(tools=self.tools, app=app)

    def __call__(
        self, appname: Optional[str] = None, update: Optional[bool] = False, **options
    ):
        # Confirm all required tools are available
        self.verify_tools()

        # Which app should we run? If there's only one defined
        # in pyproject.toml, then we can use it as a default;
        # otherwise look for a -a/--app option.
        if len(self.apps) == 1:
            app = list(self.apps.values())[0]
        elif appname:
            try:
                app = self.apps[appname]
            except KeyError as e:
                raise BriefcaseCommandError(
                    f"Project doesn't define an application named '{appname}'"
                ) from e
        else:
            raise BriefcaseCommandError(
                "Project specifies more than one application; use --app to specify which one to start."
            )

        template_file = self.bundle_path(app)
        if not template_file.exists():
            state = self.create_command(app, **options)
        else:
            state = None

        self.verify_app_tools(app)

        state = self.test_app(app, **full_options(state, options))

        return state
