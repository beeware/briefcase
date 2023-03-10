import re
import unicodedata
from email.utils import parseaddr
from typing import Optional
from urllib.parse import urlparse

from packaging.version import Version

import briefcase
from briefcase.config import (
    is_valid_app_name,
    is_valid_bundle_identifier,
    make_class_name,
)
from briefcase.exceptions import BriefcaseCommandError, TemplateUnsupportedVersion
from briefcase.integrations import git

from .base import BaseCommand


def titlecase(s):
    """Convert a string to titlecase.

    Follow Chicago Manual of Style rules for capitalization (roughly).

    * Capitalize *only* the first letter of each word
    * ... unless the word is an acronym (e.g., URL)
    * ... or the word is on the exclude list ('of', 'and', 'the)
    :param s: The input string
    :returns: A capitalized string.
    """
    return " ".join(
        word
        if (
            word.isupper()
            or word
            in {
                "a",
                "an",
                "and",
                "as",
                "at",
                "but",
                "by",
                "en",
                "for",
                "if",
                "in",
                "of",
                "on",
                "or",
                "the",
                "to",
                "via",
                "vs",
            }
        )
        else word.capitalize()
        for word in s.split(" ")
    )


class NewCommand(BaseCommand):
    cmd_line = "briefcase new"
    command = "new"
    platform = "all"
    output_format = None
    description = "Create a new Briefcase project."

    def bundle_path(self, app):
        """A placeholder; New command doesn't have a bundle path."""
        raise NotImplementedError()

    def binary_path(self, app):
        """A placeholder; New command doesn't have a binary path."""
        raise NotImplementedError()

    def parse_config(self, filename):
        """There is no configuration when starting a new project; this implementation
        overrides the base so that no config is parsed."""
        pass

    def add_options(self, parser):
        parser.add_argument(
            "-t",
            "--template",
            dest="template",
            help="The cookiecutter template to use for the new project",
        )

        parser.add_argument(
            "--template-branch",
            dest="template_branch",
            help="The branch of the cookiecutter template to use for the new project",
        )

    def make_app_name(self, formal_name):
        """Construct a candidate app name from a formal name.

        :param formal_name: The formal name
        :returns: The candidate app name
        """
        normalized = unicodedata.normalize("NFKD", formal_name)
        stripped = re.sub("[^0-9a-zA-Z_]+", "", normalized).lstrip("_")
        if stripped:
            return stripped.lower()
        else:
            # If stripping removes all the content,
            # use a dummy app name as the suggestion.
            return "myapp"

    def validate_app_name(self, candidate):
        """Determine if the app name is valid.

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
                f"A {candidate!r} directory already exists. Select a different "
                "name, move to a different parent directory, or delete the "
                "existing folder."
            )

        return True

    def make_module_name(self, app_name):
        """Construct a valid module name from an app name.

        :param app_name: The app name
        :returns: The app's module name.
        """
        return app_name.replace("-", "_")

    def validate_bundle(self, candidate):
        """Determine if the bundle identifier is valid.

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
        """Construct a candidate domain from a bundle identifier.

        :param bundle: The bundle identifier
        :returns: The candidate domain
        """
        return ".".join(bundle.split(".")[::-1])

    def make_author_email(self, author, bundle):
        """Construct a candidate email address from the authors name and the bundle
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
        return f"{author.split(' ')[0].lower()}@{self.make_domain(bundle)}"

    def validate_email(self, candidate):
        """Determine if the email address is valid.

        :param candidate: The candidate email address
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        if parseaddr(candidate)[1] != candidate:
            raise ValueError("Not a valid email address")
        return True

    def make_project_url(self, bundle, app_name):
        """Construct a candidate project URL from the bundle and app name.

        It's not a perfect guess, but it's better than having
        "https://example.com".

        :param bundle: The bundle identifier.
        :param app_name: The app name.
        :returns: The candidate project URL
        """
        return f"https://{self.make_domain(bundle)}/{app_name}"

    def validate_url(self, candidate):
        """Determine if the URL is valid.

        :param candidate: The candidate URL
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        result = urlparse(candidate)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Not a valid URL!")
        return True

    def input_text(self, intro, variable, default, validator=None):
        """Read a text answer from the user.

        :param intro: An introductory paragraph explaining the question being
            asked.
        :param variable: The name of the variable being entered.
        :param default: The default value if the user hits enter without typing
            anything.
        :param validator: (optional) A validator function; accepts a single
            input (the candidate response), returns True if the answer is
            valid, or raises ValueError() with a debugging message if the
            candidate value isn't valid.
        :returns: a string, guaranteed to meet the validation criteria of
            ``validator``.
        """
        self.input.prompt(intro)

        while True:
            self.input.prompt()

            answer = self.input.text_input(
                f"{titlecase(variable)} [{default}]: ", default=default
            )

            if validator is None:
                return answer

            try:
                validator(answer)
                return answer
            except ValueError as e:
                if not self.input.enabled:
                    raise BriefcaseCommandError(str(e)) from e
                self.input.prompt()
                self.input.prompt(f"Invalid value; {e}")

    def input_select(self, intro, variable, options):
        """Select one from a list of options.

        The first option is assumed to be the default.

        :param intro: An introductory paragraph explaining the question being
            asked.
        :param variable: The variable to display to the user.
        :param options: A list of text strings, describing the available
            options.
        :returns: The string content of the selected option.
        """
        self.input.prompt(intro)

        index_choices = [str(key) for key in range(1, len(options) + 1)]
        display_options = "\n".join(
            f"    [{index}] {option}" for index, option in zip(index_choices, options)
        )
        error_message = (
            f"Invalid selection; please enter a number between 1 and {len(options)}"
        )
        prompt = f"""
Select one of the following:

{display_options}

{titlecase(variable)} [1]: """
        selection = self.input.selection_input(
            prompt=prompt,
            choices=index_choices,
            default="1",
            error_message=error_message,
        )
        return options[int(selection) - 1]

    def build_app_context(self):
        """Ask the user for details about the app to be created.

        :returns: A context dictionary to be used in the cookiecutter project
            template.
        """
        formal_name = self.input_text(
            intro="""
First, we need a formal name for your application. This is the name that will
be displayed to humans whenever the name of the application is displayed. It
can have spaces and punctuation if you like, and any capitalization will be
used as you type it.""",
            variable="formal name",
            default="Hello World",
        )

        # The class name can be completely derived from the formal name.
        class_name = make_class_name(formal_name)

        default_app_name = self.make_app_name(formal_name)
        app_name = self.input_text(
            intro=f"""
Next, we need a name that can serve as a machine-readable Python package name
for your application. This name must be PEP508-compliant - that means the name
may only contain letters, numbers, hyphens and underscores; it can't contain
spaces or punctuation, and it can't start with a hyphen or underscore.

Based on your formal name, we suggest an app name of '{default_app_name}',
but you can use another name if you want.""",
            variable="app name",
            default=default_app_name,
            validator=self.validate_app_name,
        )

        # The module name can be completely derived from the app name.
        module_name = self.make_module_name(app_name)

        bundle = self.input_text(
            intro=f"""
Now we need a bundle identifier for your application. App stores need to
protect against having multiple applications with the same name; the bundle
identifier is the namespace they use to identify applications that come from
you. The bundle identifier is usually the domain name of your company or
project, in reverse order.

For example, if you are writing an application for Example Corp, whose website
is example.com, your bundle would be ``com.example``. The bundle will be
combined with your application's machine readable name to form a complete
application identifier (e.g., com.example.{app_name}).""",
            variable="bundle identifier",
            default="com.example",
            validator=self.validate_bundle,
        )

        project_name = self.input_text(
            intro="""
Briefcase can manage projects that contain multiple applications, so we need a
Project name. If you're only planning to have one application in this
project, you can use the formal name as the project name.""",
            variable="project name",
            default=formal_name,
        )

        description = self.input_text(
            intro="""
Now, we need a one line description for your application.""",
            variable="description",
            default="My first application",
        )

        author = self.input_text(
            intro="""
Who do you want to be credited as the author of this application? This could be
your own name, or the name of your company you work for.""",
            variable="author",
            default="Jane Developer",
        )

        author_email = self.input_text(
            intro="""
What email address should people use to contact the developers of this
application? This might be your own email address, or a generic contact address
you set up specifically for this application.""",
            variable="author's email",
            default=self.make_author_email(author, bundle),
            validator=self.validate_email,
        )

        url = self.input_text(
            intro="""
What is the website URL for this application? If you don't have a website set
up yet, you can put in a dummy URL.""",
            variable="application URL",
            default=self.make_project_url(bundle, app_name),
            validator=self.validate_url,
        )

        project_license = self.input_select(
            intro="""
What license do you want to use for this project's code?""",
            variable="project license",
            options=[
                "BSD license",
                "MIT license",
                "Apache Software License",
                "GNU General Public License v2 (GPLv2)",
                "GNU General Public License v2 or later (GPLv2+)",
                "GNU General Public License v3 (GPLv3)",
                "GNU General Public License v3 or later (GPLv3+)",
                "Proprietary",
                "Other",
            ],
        )

        gui_framework = self.input_select(
            intro="""
What GUI toolkit do you want to use for this project?""",
            variable="GUI framework",
            options=[
                "Toga",
                "PySide2 (does not support iOS/Android deployment)",
                "PySide6 (does not support iOS/Android deployment)",
                "PursuedPyBear (does not support iOS/Android deployment)",
                "Pygame (does not support iOS/Android deployment)",
                "None",
            ],
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

    def new_app(
        self,
        template: Optional[str] = None,
        template_branch: Optional[str] = None,
        **options,
    ):
        """Ask questions to generate a new application, and generate a stub project from
        the briefcase-template."""
        if template is None:
            template = "https://github.com/beeware/briefcase-template"

        self.input.prompt()
        self.input.prompt("Let's build a new Briefcase app!")
        self.input.prompt()

        context = self.build_app_context()

        self.logger.info()
        self.logger.info(f"Generating a new application '{context['formal_name']}'")

        # If a branch wasn't supplied through the --template-branch argument,
        # use the branch derived from the Briefcase version
        version = Version(briefcase.__version__)
        if template_branch is None:
            branch = f"v{version.base_version}"
        else:
            branch = template_branch

        # Make extra sure we won't clobber an existing application.
        if (self.base_path / context["app_name"]).exists():
            raise BriefcaseCommandError(
                f"A directory named '{context['app_name']}' already exists."
            )

        # This is to have briefcase template file
        # mentioning extra context on which template/branch
        # the project was generated from.
        context.update({"template": template, "branch": branch})

        try:
            self.logger.info(f"Using app template: {template}, branch {branch}")
            # Unroll the new app template
            self.generate_template(
                template=template,
                branch=branch,
                output_path=self.base_path,
                extra_context=context,
            )
        except TemplateUnsupportedVersion:
            # If we're *not* on a development branch, raise an error about
            # the missing template branch.
            if version.dev is None:
                raise

            # Development branches can use the main template.
            self.logger.info(
                f"Template branch {branch} not found; falling back to development template"
            )
            branch = "main"
            self.generate_template(
                template=template,
                branch=branch,
                output_path=self.base_path,
                extra_context=context,
            )

        self.logger.info(
            f"""
Application '{context['formal_name']}' has been generated. To run your application, type:

    cd {context['app_name']}
    briefcase dev
"""
        )

    def verify_tools(self):
        """Verify that the tools needed to run this command exist.

        Raises MissingToolException if a required system tool is missing.
        """
        super().verify_tools()
        git.verify_git_is_installed(tools=self.tools)

    def __call__(
        self,
        template: Optional[str] = None,
        template_branch: Optional[str] = None,
        **options,
    ):
        # Confirm host compatibility, and that all required tools are available.
        # There are no apps, so finalize() will be a no op on app configurations.
        self.finalize()

        return self.new_app(
            template=template, template_branch=template_branch, **options
        )
