import os
import re
import subprocess
import unicodedata
from email.utils import parseaddr
from typing import Optional
from urllib.parse import urlparse

from cookiecutter import exceptions as cookiecutter_exceptions

from briefcase.config import is_valid_app_name, is_valid_bundle_identifier
from briefcase.exceptions import NetworkFailure

from .base import BaseCommand, BriefcaseCommandError
from .create import InvalidTemplateRepository


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

    def distribution_path(self, app, packaging_format):
        "A placeholder; New command doesn't have a distribution path"
        raise NotImplementedError()

    def parse_config(self, filename):
        """
        There is no configuration when starting a new project;
        this implementation overrides the base so that no config is parsed.
        """
        pass

    def add_options(self, parser):
        parser.add_argument(
            '-t',
            '--template',
            dest='template',
            help='The cookiecutter template to use for the new project'
        )

    def make_class_name(self, formal_name):
        """
        Construct a valid class name from a formal name.

        :param formal_name: The formal name
        :returns: The app's class name
        """
        # Identifiers (including class names) can be unicode.
        # https://docs.python.org/3/reference/lexical_analysis.html#identifiers
        xid_start = {
            "Lu",  # uppercase letters
            "Ll",  # lowercase letters
            "Lt",  # titlecase letters
            "Lm",  # modifier letters
            "Lo",  # other letters
            "Nl",  # letter numbers
        }
        xid_continue = xid_start.union({
            "Mn",  # nonspacing marks
            "Mc",  # spacing combining marks
            "Nd",  # decimal number
            "Pc",  # connector punctuations
        })

        # Normalize to NFKC form, then remove any character that isn't
        # in the allowed categories, or is the underscore character
        class_name = ''.join(
            ch for ch in unicodedata.normalize('NFKC', formal_name)
            if unicodedata.category(ch) in xid_continue
            or ch in {'_'}
        )

        # If the first character isn't in the 'start' character set,
        # and it isn't already an underscore, prepend an underscore.
        if unicodedata.category(class_name[0]) not in xid_start and class_name[0] != '_':
            class_name = '_' + class_name

        return class_name

    def make_app_name(self, formal_name):
        """
        Construct a candidate app name from a formal name.

        :param formal_name: The formal name
        :returns: The candidate app name
        """
        normalized = unicodedata.normalize('NFKD', formal_name)
        stripped = re.sub('[^0-9a-zA-Z_]+', '', normalized).lstrip('_')
        if stripped:
            return stripped.lower()
        else:
            # If stripping removes all the content,
            # use a dummy app name as the suggestion.
            return 'myapp'

    def validate_app_name(self, candidate):
        """
        Determine if the app name is valid.

        :param candidate: The candidate name
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        if not is_valid_app_name(candidate):
            raise ValueError(
                f"{candidate!r} is not a valid app name.\n\n"
                "App names must not be reserved keywords such as 'and', 'for' and 'while'.\n"
                "They must also be PEP508 compliant (i.e., they can only include letters,\n"
                "numbers, '-' and '_'; must start with a letter; and cannot end with '-' or '_')."
            )

        if (self.base_path / candidate).exists():
            raise ValueError(
                f"A '{candidate!r}' directory already exists. Select a different "
                "name, move to a different parent directory, or delete the "
                "existing folder."
            )

        return True

    def make_module_name(self, app_name):
        """
        Construct a valid module name from an app name.

        :param app_name: The app name
        :returns: The app's module name.
        """
        module_name = app_name.replace('-', '_')
        return module_name

    def validate_bundle(self, candidate):
        """
        Determine if the bundle identifier is valid.

        :param candidate: The candidate bundle identifier
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        if not is_valid_bundle_identifier(candidate):
            raise ValueError(
                f"{candidate!r} is not a valid bundle identifier.\n\n"
                "The bundle should be a reversed domain name. It must contain at least 2\n"
                "dot-separated sections; each section may only include letters, numbers,\n"
                "and hyphens; and each section may not contain any reserved words (like\n"
                "'switch', or 'while')."
            )

        return True

    def make_domain(self, bundle):
        """
        Construct a candidate domain from a bundle identifier.

        :param bundle: The bundle identifier
        :returns: The candidate domain
        """
        return '.'.join(bundle.split('.')[::-1])

    def make_author_email(self, author, bundle):
        """
        Construct a candidate email address from the authors name and the bundle
        identifier.

        The candidate is based on the assumption that the author's name is in
        "first/last" format, or it a corporate name; the "first" part is split
        off, and prepended to the domain extracted from the bundle.

        It's not a perfect system, but it's better than putting up
        "me@example.com" as a candidate default value.

        :param author: The authors name.
        :param bundle: The bundle identifier.
        :returns: The candidate author's name
        """
        return '{first_name}@{domain}'.format(
            first_name=author.split(' ')[0].lower(),
            domain=self.make_domain(bundle),
        )

    def validate_email(self, candidate):
        """
        Determine if the email address is valid.

        :param candidate: The candidate email address
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        if parseaddr(candidate)[1] != candidate:
            raise ValueError('Not a valid email address')
        return True

    def make_project_url(self, bundle, app_name):
        """
        Construct a candidate project URL from the bundle and app name.

        It's not a perfect guess, but it's better than having
        "https://example.com".

        :param bundle: The bundle identifier.
        :param app_name: The app name.
        :returns: The candidate project URL
        """
        return 'https://{domain}/{app_name}'.format(
            domain=self.make_domain(bundle),
            app_name=app_name
        )

    def validate_url(self, candidate):
        """
        Determine if the URL is valid.

        :param candidate: The candidate URL
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        result = urlparse(candidate)
        if not all([result.scheme, result.netloc]):
            raise ValueError('Not a valid URL!')
        return True

    def build_app_context(self):
        """
        Ask the user for details about the app to be created.

        :returns: A context dictionary to be used in the cookiecutter project
            template.
        """
        formal_name = self.input.text_input(
            intro="""
First, we need a formal name for your application. This is the name that will
be displayed to humans whenever the name of the application is displayed. It
can have spaces and punctuation if you like, and any capitalization will be
used as you type it.""",
            input_name="formal name",
            default='Hello World',
        )

        # The class name can be completely derived from the formal name.
        class_name = self.make_class_name(formal_name)

        default_app_name = self.make_app_name(formal_name)
        app_name = self.input.text_input(
            intro="""
Next, we need a name that can serve as a machine-readable Python package name
for your application. This name must be PEP508-compliant - that means the name
may only contain letters, numbers, hyphens and underscores; it can't contain
spaces or punctuation, and it can't start with a hyphen or underscore.

Based on your formal name, we suggest an app name of '{default_app_name}',
but you can use another name if you want.""".format(
                default_app_name=default_app_name
            ),
            input_name="app name",
            default=default_app_name,
            validator=self.validate_app_name,
        )

        # The module name can be completely derived from the app name.
        module_name = self.make_module_name(app_name)

        bundle = self.input.text_input(
            intro="""
Now we need a bundle identifier for your application. App stores need to
protect against having multiple applications with the same name; the bundle
identifier is the namespace they use to identify applications that come from
you. The bundle identifier is usually the domain name of your company or
project, in reverse order.

For example, if you are writing an application for Example Corp, whose website
is example.com, your bundle would be ``com.example``. The bundle will be
combined with your application's machine readable name to form a complete
application identifier (e.g., com.example.{app_name}).""".format(
                app_name=app_name,
            ),
            input_name="bundle identifier",
            default='com.example',
            validator=self.validate_bundle,
        )

        project_name = self.input.text_input(
            intro="""
Briefcase can manage projects that contain multiple applications, so we need a
Project name. If you're only planning to have one application in this
project, you can use the formal name as the project name.""",
            input_name="project name",
            default=formal_name
        )

        description = self.input.text_input(
            intro="""
Now, we need a one line description for your application.""",
            input_name="description",
            default="My first application"
        )

        author = self.input.text_input(
            intro="""
Who do you want to be credited as the author of this application? This could be
your own name, or the name of your company you work for.""",
            input_name="author",
            default="Jane Developer",
        )

        author_email = self.input.text_input(
            intro="""
What email address should people use to contact the developers of this
application? This might be your own email address, or a generic contact address
you set up specifically for this application.""",
            input_name="author's email",
            default=self.make_author_email(author, bundle),
            validator=self.validate_email
        )

        url = self.input.text_input(
            intro="""
What is the website URL for this application? If you don't have a website set
up yet, you can put in a dummy URL.""",
            input_name="application URL",
            default=self.make_project_url(bundle, app_name),
            validator=self.validate_url
        )

        project_license = self.input.selection_input(
            intro="""
What license do you want to use for this project's code?""",
            input_name="project license",
            default="BSD license",
            options=(
                "BSD license",
                "MIT license",
                "Apache Software License",
                "GNU General Public License v2 (GPLv2)",
                "GNU General Public License v2 or later (GPLv2+)",
                "GNU General Public License v3 (GPLv3)",
                "GNU General Public License v3 or later (GPLv3+)",
                "Proprietary",
                "Other"
            ),
        )

        gui_framework = self.input.selection_input(
            intro="""
What GUI toolkit do you want to use for this project?""",
            input_name="GUI framework",
            default="Toga",
            options=(
                "Toga",
                "PySide2 (does not support iOS/Android deployment)",
                "PySide6 (does not support iOS/Android deployment)",
                "PursuedPyBear (does not support iOS/Android deployment)",
                "None",
            ),
        )

        return {
            "formal_name": formal_name,
            "app_name": app_name,
            "class_name": class_name,
            "module_name": module_name,
            "project_name": project_name,
            "description": description,
            "author": author,
            "author_email": author_email,
            "bundle": bundle,
            "url": url,
            "license": project_license,
            "gui_framework": (gui_framework.split())[0],
        }

    def new_app(self, template: Optional[str] = None, **options):
        """
        Ask questions to generate a new application, and generate a stub
        project from the briefcase-template.
        """
        if template is None:
            template = 'https://github.com/beeware/briefcase-template'

        self.input.print()
        self.input.print("Let's build a new Briefcase app!")
        self.input.print()

        context = self.build_app_context()

        self.logger.info()
        self.logger.info("Generating a new application '{formal_name}'".format(
            **context
        ))

        cached_template = self.update_cookiecutter_cache(
            template=template,
            branch='v0.3'
        )

        # Make extra sure we won't clobber an existing application.
        if (self.base_path / context['app_name']).exists():
            raise BriefcaseCommandError(
                "A directory named '{app_name}' already exists.".format(
                    **context
                )
            )

        try:
            # Unroll the new app template
            self.cookiecutter(
                str(cached_template),
                no_input=True,
                output_dir=os.fsdecode(self.base_path),
                checkout="v0.3",
                extra_context=context
            )
        except subprocess.CalledProcessError:
            # Computer is offline
            # status code == 128 - certificate validation error.
            raise NetworkFailure("clone template repository")
        except cookiecutter_exceptions.RepositoryNotFound:
            # Either the template path is invalid,
            # or it isn't a cookiecutter template (i.e., no cookiecutter.json)
            raise InvalidTemplateRepository(template)

        self.logger.info("""
Application '{formal_name}' has been generated. To run your application, type:

    cd {app_name}
    briefcase dev
""".format(**context))

    def verify_tools(self):
        """
        Verify that the tools needed to run this command exist

        Raises MissingToolException if a required system tool is missing.
        """
        self.git = self.integrations.git.verify_git_is_installed(self)

    def __call__(
        self,
        template: Optional[str] = None,
        **options
    ):
        # Confirm all required tools are available
        self.verify_tools()

        state = self.new_app(template=template, **options)
        return state
