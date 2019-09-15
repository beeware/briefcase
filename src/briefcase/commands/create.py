import subprocess
from abc import abstractmethod
from datetime import date
from pathlib import Path

from git import exc as git_exceptions
from cookiecutter import exceptions as cookiecutter_exceptions

from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand


class TemplateUnsupportedPythonVersion(BriefcaseCommandError):
    def __init__(self, version_tag):
        self.version_tag = version_tag
        super().__init__(
            msg='Template does not support Python version {version_tag}'.format(
                version_tag=version_tag
            )
        )


class NetworkFailure(BriefcaseCommandError):
    def __init__(self, action):
        self.action = action
        super().__init__(msg="Uunable to {action}; is your computer offline?".format(
            action=action
        ))


class InvalidTemplateRepository(BriefcaseCommandError):
    def __init__(self, template):
        self.template = template
        super().__init__(
            'Unable to clone application template; is the template path {template!r} correct?'.format(
                template=template
            )
        )


def cookiecutter_cache_path(template):
    """
    Determine the cookiecutter template cache directory given a template URL.

    This will return a valid path, regardless of whether `template`

    :param template: The template to use. This can be a filesystem path or
        a URL.
    :returns: The path that cookiecutter would use for the given template name.
    """
    template = template.rstrip('/')
    tail = template.split('/')[-1]
    cache_name = tail.rsplit('.git')[0]
    return Path.home() / '.cookiecutters' / cache_name


class CreateCommand(BaseCommand):
    @property
    @abstractmethod
    def template_url(self):
        "The URL for a cookiecutter repository to use when creating apps"
        ...

    @abstractmethod
    def bundle_path(self, app, base):
        """
        The path to the bundle for the app in the output format.

        The bundle is the template-generated source form of the app.
        """
        ...

    @abstractmethod
    def binary_path(self, app, base):
        """
        The path to the executable artefact for the app in the output format

        This *may* be the same as the bundle path, if the output format
        requires no compilation, or if it compiles in place.
        """
        ...

    @abstractmethod
    def verify_tools(self):
        "Verify that the tools needed to run this command exist"

    def generate_app_template(self, app, path):
        # If the app config doesn't explicitly define a template,
        # use a default template.
        if app.template is None:
            app.template = self.template_url

        print("Using app template: {app_template}".format(
            app_template=app.template,
        ))

        # When in `no_input=True` mode, cookiecutter deletes and reclones
        # a template directory, rather than updating the existing repo.

        # Look for a cookiecutter cache of the template; if one exists,
        # try to update it using git. If no cache exists, or if the cache
        # directory isn't a git directory, or git fails for some reason,
        # fall back to using the specified template directly.
        try:
            template = cookiecutter_cache_path(app.template)
            repo = self.git.Repo(template)
            try:
                # Attempt to update the repository
                remote = repo.remote(name='origin')
                remote.fetch()
            except git_exceptions.GitCommandError:
                # We are offline, or otherwise unable to contact
                # the origin git repo. It's OK to continue; but warn
                # the user that the template may be stale.
                print("***************************************************************************")
                print("WARNING: Unable to update application template (is your computer offline?)")
                print("WARNING: Briefcase will use existing template without updating.")
                print("***************************************************************************")
            try:
                # Check out the branch for the required version tag.
                head = repo.heads[self.python_version_tag]
                print("Using existing template {hexsha} (updated {datestamp})".format(
                    hexsha=head.commit.hexsha,
                    datestamp=head.commit.committed_datetime.strftime("%c")
                ))
                head.checkout()
            except IndexError:
                # No branch exists for the requested version.
                raise TemplateUnsupportedPythonVersion(self.python_version_tag)
        except git_exceptions.NoSuchPathError:
            # Template cache path doesn't exist.
            # Just use the template directly, rather than attempting an update.
            template = app.template
        except git_exceptions.InvalidGitRepositoryError:
            # Template cache path exists, but isn't a git repository
            # Just use the template directly, rather than attempting an update.
            template = app.template

        # Construct a template context from the app configuration.
        # Augment with some extra fields.
        extra_context = app.__dict__.copy()
        extra_context.update({
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        })

        try:
            self.cookiecutter(
                template,
                no_input=True,
                # output_dir=path,
                checkout=self.python_version_tag,
                extra_context=extra_context
            )
        except subprocess.CalledProcessError:
            # Computer is offline
            raise NetworkFailure("clone template repository")
        except cookiecutter_exceptions.RepositoryNotFound:
            # Either the template path is invalid,
            # or it isn't a cookiecutter template (i.e., no cookiecutter.json)
            raise InvalidTemplateRepository(app.template)
        except cookiecutter_exceptions.RepositoryCloneFailed:
            # Branch does not exist for python version
            raise TemplateUnsupportedPythonVersion(self.python_version_tag)

    def install_app_support_package(self, app, path):
        pass

    def install_app_dependencies(self, app, path):
        pass

    def install_app_code(self, app, path):
        pass

    def install_app_extras(self, app, path):
        pass

    def create_app(self, app, path=None):
        bundle_path = self.bundle_path(app=app, base=path)
        if bundle_path.exists():
            confirm = input('Application {} already exists; overwrite (y/N)? '.format(
                app_name=app.name
            ))
            if confirm.lower() != 'y':
                print("Aborting creation of app {app_name}".format(
                    app_name=app.name
                ))
                return
            print("[{app_name} Removing old application bundle...".format(
                app_name=app.name
            ))
            bundle_path.rmdir()

        print('[{app_name}] Generate application template...'.format(
            app_name=app.name
        ))
        self.generate_app_template(app=app, path=bundle_path)
        print('[{app_name}] Install support package...'.format(
            app_name=app.name
        ))
        self.install_app_support_package(app=app, path=bundle_path)
        print('[{app_name}] Install dependencies...'.format(
            app_name=app.name
        ))
        self.install_app_dependencies(app=app, path=bundle_path)
        print('[{app_name}] Install application code...'.format(
            app_name=app.name
        ))
        self.install_app_code(app=app, path=bundle_path)
        print('[{app_name}] Install extra resources...'.format(
            app_name=app.name
        ))
        self.install_app_extras(app=app, path=bundle_path)

    def create_project(self, app):
        pass

    def __call__(self, path=None):
        if path is None:
            path = Path.cwd()

        self.verify_tools()

        for app_name, app in self.apps.items():
            self.create_app(app, path)
