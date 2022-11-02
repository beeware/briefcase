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

    def install_test_code(self, app: BaseConfig):
        """Install the application test code into the bundle.

        :param app: The config object for the app
        """
        # Remove existing test folder if it exists
        tests_path = self.tests_path(app)
        if tests_path.exists():
            self.tools.shutil.rmtree(tests_path)
        self.tools.os.mkdir(tests_path)

        # Install app test code.
        if app.test_sources:
            for src in app.test_sources:
                with self.input.wait_bar(f"Installing {src}..."):
                    original = self.base_path / src
                    target = tests_path

                    # Install the new copy of the app test code.
                    if not original.exists():
                        raise MissingTestSources(src)
                    elif original.is_dir():
                        for f in original.iterdir():
                            if f.is_dir():
                                self.tools.shutil.copytree(f, target / f.name)
                            else:
                                self.tools.shutil.copy(f, target / f.name)
                    else:
                        self.tools.shutil.copy(original, target / original.name)
        else:
            raise BriefcaseCommandError("No test sources for app")

    def install_test_dependencies(self, app: BaseConfig):
        """Handle test dependencies for the app.

        This will result in either (in preferential order):
         * a requirements.txt file being written at a location specified by
           ``app_requirements_path`` in the template path index
         * dependencies being installed with pip into the location specified
           by the ``app_packages_path`` in the template path index.

        If the path index doesn't specify either of the path index entries,
        an error is raised.

        :param app: The config object for the app
        """
        try:
            test_packages_path = self.test_requirements_path(app)
            self.write_requirements_file(
                "test",
                app=app,
                requires=app.test_requires,
                path=test_packages_path,
            )
        except KeyError:
            try:
                test_packages_path = self.test_packages_path(app)
                self.install_dependencies(
                    "test",
                    app=app,
                    requires=app.test_requires,
                    path=test_packages_path,
                )
            except KeyError as e:
                raise BriefcaseCommandError(
                    "Application path index file does not define "
                    "`test_requirements_path` or `test_packages_path`"
                ) from e

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
        binary_file = self.binary_path(app)
        if not template_file.exists():
            state = self.create_command(app, **options)
            state = self.build_command(app, **full_options(state, options))
        elif update:
            state = self.update_command(app, **options)
            state = self.build_command(app, **full_options(state, options))
        elif not binary_file.exists():
            state = self.build_command(app, **options)
        else:
            state = None

        self.verify_app_tools(app)

        state = self.test_app(app, **full_options(state, options))

        return state
