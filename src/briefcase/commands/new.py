from __future__ import annotations

import re
import sys
import unicodedata
from collections import OrderedDict
from collections.abc import Sequence
from email.utils import parseaddr
from typing import Iterable
from urllib.parse import urlparse

if sys.version_info >= (3, 10):  # pragma: no-cover-if-lt-py310
    from importlib.metadata import entry_points
else:  # pragma: no-cover-if-gte-py310
    # Before Python 3.10, entry_points did not support the group argument;
    # so, the backport package must be used on older versions.
    from importlib_metadata import entry_points

from briefcase.bootstraps import BaseGuiBootstrap
from briefcase.config import (
    is_valid_app_name,
    is_valid_bundle_identifier,
    make_class_name,
)
from briefcase.console import MAX_TEXT_WIDTH
from briefcase.console import select_option as _select_option
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.git import Git

from .base import BaseCommand


def titlecase(s):
    """Convert a string to titlecase.

    Follow Chicago Manual of Style rules for capitalization (roughly).

    * Capitalize *only* the first letter of each word
    * ... unless the word is an acronym (e.g., URL)
    * ... or the word is on the exclude list ('of', 'and', 'the')
    :param s: The input string
    :returns: A capitalized string.
    """
    return " ".join(
        (
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
        )
        for word in s.split(" ")
    )


def get_gui_bootstraps() -> dict[str, type[BaseGuiBootstrap]]:
    """Loads built-in and third-party GUI bootstraps."""
    return {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="briefcase.bootstraps")
    }


def parse_project_overrides(project_overrides: list[str]) -> dict[str, str]:
    """Parse the command-line arguments to override new project defaults."""
    overrides = {}

    if project_overrides:
        for override in project_overrides:
            try:
                key, value = override.split("=", 1)
            except ValueError as e:
                raise BriefcaseCommandError(
                    f"Unable to parse project configuration override {override!r}"
                ) from e
            else:
                if not ((key := key.strip()) and (value := value.strip())):
                    raise BriefcaseCommandError(
                        f"Invalid Project configuration override {override!r}"
                    )
                if key in overrides:
                    raise BriefcaseCommandError(
                        f"Project configuration override {key!r} specified multiple times"
                    )
                overrides[key] = value
    return overrides


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

    def parse_config(self, filename, overrides):
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

        parser.add_argument(
            "-Q",
            dest="project_overrides",
            action="append",
            metavar="KEY=VALUE",
            help="Override the value of the project configuration item KEY with VALUE",
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

    def validate_formal_name(self, candidate):
        """Determine if the formal name is valid.

        A formal name is valid if it contains at least one identifier character.

        :param candidate: The candidate name
        :returns: True the formal name is valid.
        :raises: ValueError if the name is not a valid formal name.
        """
        if not make_class_name(candidate):  # Check whether a class name may be derived
            raise ValueError(
                self.input.textwrap(
                    f"{candidate!r} is not a valid formal name.\n"
                    "\n"
                    "Formal names must include at least one valid Python identifier character."
                )
            )

        return True

    def _validate_existing_app_name(self, candidate):
        """Perform internal validation preventing the use of pre-existing app names.

        Invoked by validate_app_name; subclasses may override this behavior.
        """
        if (self.base_path / candidate).exists():
            raise ValueError(
                self.input.textwrap(
                    f"A {candidate!r} directory already exists.\n"
                    f"\n"
                    f"Select a different name, move to a different parent directory, or "
                    f"delete the existing folder."
                )
            )

    def validate_app_name(self, candidate):
        """Determine if the app name is valid.

        :param candidate: The candidate name
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
        """
        if not is_valid_app_name(candidate):
            raise ValueError(
                self.input.textwrap(
                    f"{candidate!r} is not a valid app name.\n"
                    "\n"
                    "App names must not be reserved keywords such as 'and', 'for' and "
                    "'while'. They must also be PEP508 compliant (i.e., they can only "
                    "include letters, numbers, '-' and '_'; must start with a letter; "
                    "and cannot end with '-' or '_')."
                )
            )

        # Validate if the existing app name
        self._validate_existing_app_name(candidate)

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
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
        """
        if not is_valid_bundle_identifier(candidate):
            raise ValueError(
                self.input.textwrap(
                    f"{candidate!r} is not a valid bundle identifier.\n"
                    "\n"
                    "The bundle should be a reversed domain name. It must contain at "
                    "least 2 dot-separated sections; each section may only include "
                    "letters, numbers, and hyphens; and each section may not contain any "
                    "reserved words (like 'switch', or 'while')."
                )
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
        "first/last" format, or it a corporate name; the "first" part is split off, and
        prepended to the domain extracted from the bundle.

        It's not a perfect system, but it's better than putting up "me@example.com" as a
        candidate default value.

        :param author: The authors name.
        :param bundle: The bundle identifier.
        :returns: The candidate author's name
        """
        return f"{author.split(' ')[0].lower()}@{self.make_domain(bundle)}"

    def validate_email(self, candidate):
        """Determine if the email address is valid.

        :param candidate: The candidate email address
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
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
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
        """
        result = urlparse(candidate)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Not a valid URL!")
        if result.scheme not in {"http", "https"}:
            raise ValueError("Not a valid website URL!")
        return True

    def prompt_divider(self, title: str = ""):
        """Writes a divider with an optional title."""
        title = f"-- {title} " if title else ""
        self.input.prompt()
        self.input.prompt()
        self.input.prompt(f"{title}{'-' * (MAX_TEXT_WIDTH - len(title))}", style="bold")

    def prompt_intro(self, intro: str):
        """Write the introduction for a prompt."""
        self.input.prompt()
        self.input.prompt(self.input.textwrap(intro))
        self.input.prompt()

    def validate_user_input(self, validator, answer) -> bool:
        """Validate a user's input is acceptable.

        A warning message is issued if input is enabled. Otherwise, an exception is
        raised and project creation is aborted.
        """
        error_msg = f"Invalid value; {answer}"
        try:
            if validator is None or validator(answer):
                return True
        except ValueError as e:
            error_msg = str(e)

        if not self.input.enabled:
            raise BriefcaseCommandError(error_msg)
        self.logger.warning()
        self.logger.warning(error_msg)

        return False

    def validate_override(self, override_value: str | None, validator=None) -> bool:
        """Validates and returns override value for a project configuration."""
        if override_value is not None:
            self.input.prompt()
            self.input.prompt(f"Using override value {override_value!r}")
            if not self.validate_user_input(validator, override_value):
                return False
        return True

    def validate_selection_override(
        self,
        choices: Iterable[str],
        override_value: str | None,
    ) -> bool:
        """Validate a project override value against a list of options."""
        return self.validate_override(override_value, validator=lambda c: c in choices)

    def input_text(self, intro, variable, default, validator=None, override_value=None):
        """Read a text answer from the user.

        :param intro: An introductory paragraph explaining the question being asked.
        :param variable: The name of the variable being entered.
        :param default: The default value if the user hits enter without typing anything.
        :param validator: (optional) A validator function; accepts a single input (the
            candidate response), returns True if the answer is valid, or raises
            ValueError() with a debugging message if the candidate value isn't valid.
        :param override_value: value to return instead of soliciting input
        :returns: a string, guaranteed to meet the validation criteria of ``validator``
        """
        variable = titlecase(variable)
        self.prompt_divider(title=variable)

        if override_value and self.validate_override(override_value, validator):
            return override_value

        self.prompt_intro(intro=intro)
        while True:
            answer = self.input.text_input(f"{variable} [{default}]: ", default=default)

            if self.validate_user_input(validator, answer):
                return answer

            self.input.prompt()

    def select_option(
        self,
        intro: str,
        variable: str,
        default: str | None,
        options: Sequence[str],
        override_value: str | None,
    ) -> str:
        variable = titlecase(variable)
        self.prompt_divider(title=variable)

        if override_value is not None:
            if self.validate_selection_override(options, override_value):
                return override_value
            else:
                self.logger.warning(
                    f"Invalid override value {override_value!r} for {variable}, using user-provided value."
                )

        if default is not None:
            default = str(options.index(default) + 1)
        else:
            default = "1"

        self.prompt_intro(intro=intro)
        return _select_option(
            prompt=f"{variable} [{default}]:",
            input=self.input,
            default=default,
            options=list(zip(options, options)),
        )

    def input_project_name(self, formal_name, override_value):
        return self.input_text(
            intro=(
                "Briefcase can manage projects that contain multiple applications, so "
                "we need a Project name.\n"
                "\n"
                "If you're only planning to have one application in this project, you "
                "can use the formal name as the project name."
            ),
            variable="project name",
            default=formal_name,
            override_value=override_value,
        )

    def input_license(self, override_value: str | None):
        licenses = [
            "BSD license",
            "MIT license",
            "Apache Software License",
            "GNU General Public License v2 (GPLv2)",
            "GNU General Public License v2 or later (GPLv2+)",
            "GNU General Public License v3 (GPLv3)",
            "GNU General Public License v3 or later (GPLv3+)",
            "Proprietary",
            "Other",
        ]
        return self.select_option(
            intro="What license do you want to use for this project's code?",
            variable="Project License",
            options=licenses,
            default=None,
            override_value=override_value,
        )

    def build_context(self, project_overrides: dict[str, str]) -> dict[str, str]:
        """Builds the cookiecutter context dict for the new project."""
        context = self.build_app_context(project_overrides)
        context.update(self.build_gui_context(context, project_overrides))

        return context

    def build_app_context(self, project_overrides: dict[str, str]) -> dict[str, str]:
        """Ask the user for details about the app to be created.

        :returns: A context dictionary to be used in the cookiecutter project template.
        """
        formal_name = self.input_text(
            intro=(
                "First, we need a formal name for your application.\n"
                "\n"
                "This is the name that will be displayed to humans whenever the name "
                "of the application is displayed. It can have spaces and punctuation "
                "if you like, and any capitalization will be used as you type it."
            ),
            variable="formal name",
            default="Hello World",
            validator=self.validate_formal_name,
            override_value=project_overrides.pop("formal_name", None),
        )

        # The class name can be completely derived from the formal name.
        class_name = make_class_name(formal_name)

        default_app_name = self.make_app_name(formal_name)
        app_name = self.input_text(
            intro=(
                "Next, we need a name that can serve as a machine-readable Python "
                "package name for your application.\n"
                "\n"
                "This name must be PEP508-compliant - that means the name may only "
                "contain letters, numbers, hyphens and underscores; it can't contain "
                "spaces or punctuation, and it can't start with a hyphen or "
                "underscore.\n"
                "\n"
                "Based on your formal name, we suggest an app name of "
                f"{default_app_name!r}, but you can use another name if you want."
            ),
            variable="app name",
            default=default_app_name,
            validator=self.validate_app_name,
            override_value=project_overrides.pop("app_name", None),
        )

        # The module name can be completely derived from the app name.
        module_name = self.make_module_name(app_name)
        source_dir = f"src/{module_name}"
        test_source_dir = "tests"

        bundle = self.input_text(
            intro=(
                "Now we need a bundle identifier for your application.\n"
                "\n"
                "App stores need to protect against having multiple applications with "
                "the same name; the bundle identifier is the namespace they use to "
                "identify applications that come from you. The bundle identifier is "
                "usually the domain name of your company or project, in reverse order.\n"
                "\n"
                "For example, if you are writing an application for Example Corp, "
                "whose website is example.com, your bundle would be 'com.example'. "
                "The bundle will be combined with your application's machine readable "
                "name to form a complete application identifier (e.g., "
                f"com.example.{app_name})."
            ),
            variable="bundle identifier",
            default="com.example",
            validator=self.validate_bundle,
            override_value=project_overrides.pop("bundle", None),
        )

        project_name = self.input_project_name(
            formal_name, project_overrides.pop("project_name", None)
        )

        description = self.input_text(
            intro="Now, we need a one line description for your application.",
            variable="description",
            default="My first application",
            override_value=project_overrides.pop("description", None),
        )

        author = self.input_text(
            intro=(
                "Who do you want to be credited as the author of this application?\n"
                "\n"
                "This could be your own name, or the name of your company you work for."
            ),
            variable="author",
            default="Jane Developer",
            override_value=project_overrides.pop("author", None),
        )

        author_email = self.input_text(
            intro=(
                "What email address should people use to contact the developers of "
                "this application?\n"
                "\n"
                "This might be your own email address, or a generic contact address "
                "you set up specifically for this application."
            ),
            variable="author's email",
            default=self.make_author_email(author, bundle),
            validator=self.validate_email,
            override_value=project_overrides.pop("author_email", None),
        )

        url = self.input_text(
            intro=(
                "What is the website URL for this application?\n"
                "\n"
                "If you don't have a website set up yet, you can put in a dummy URL."
            ),
            variable="application URL",
            default=self.make_project_url(bundle, app_name),
            validator=self.validate_url,
            override_value=project_overrides.pop("url", None),
        )
        project_license = self.input_license(
            override_value=project_overrides.pop("license", None)
        )

        return {
            "formal_name": formal_name,
            "app_name": app_name,
            "class_name": class_name,
            "module_name": module_name,
            "source_dir": source_dir,
            "test_source_dir": test_source_dir,
            "project_name": project_name,
            "description": description,
            "author": author,
            "author_email": author_email,
            "bundle": bundle,
            "url": url,
            "license": project_license,
        }

    def build_gui_context(
        self,
        context: dict[str, str],
        project_overrides: dict[str, str],
    ) -> dict[str, str]:
        """Build context specific to the GUI toolkit."""
        bootstraps = get_gui_bootstraps()
        bootstrap_options = self._gui_bootstrap_choices(bootstraps)

        # Map the override value to the annotated override value so we can use it with self.select_option
        # If a user specifies the override value PySide6, then we want it to be mapped to the annotated value
        # "PySide6       (does not support iOS/Android deployment)"
        # since that is the option presented to the user. To accomplish this, we map the bootstrap classes
        # to their annotated names and do a reverse lookup from the override bootstrap class to the annotated name.
        #
        # We do it this way to ensure consistent prompting for the user.
        if bootstrap_override := project_overrides.pop("bootstrap", None):
            reverse_lookup = {v: k for k, v in bootstrap_options.items()}
            if self.validate_selection_override(bootstraps.keys(), bootstrap_override):
                bootstrap_override = reverse_lookup[bootstraps[bootstrap_override]]

        selected_bootstrap = self.select_option(
            intro=(
                "What GUI toolkit do you want to use for this project?\n"
                "\n"
                "Additional GUI bootstraps are available; visit "
                "https://beeware.org/bee/briefcase-bootstraps "
                "for a full list of known GUI bootstraps."
            ),
            variable="GUI Framework",
            default=None,
            options=bootstrap_options.keys(),
            override_value=bootstrap_override,
        )
        bootstrap_class = bootstrap_options[selected_bootstrap]

        gui_context = {}

        if bootstrap_class is not None:
            bootstrap: BaseGuiBootstrap = bootstrap_class(context=context)

            # Iterate over the Bootstrap interface to build the context.
            # Returning ``None`` is a special case that means the field should not be
            # included in the context and instead deferred to the template default.

            if hasattr(bootstrap, "extra_context"):
                if (additional_context := bootstrap.extra_context()) is not None:
                    gui_context.update(additional_context)

            for context_field in bootstrap.fields:
                if (context_value := getattr(bootstrap, context_field)()) is not None:
                    gui_context[context_field] = context_value

        return gui_context

    def _gui_bootstrap_choices(self, bootstraps):
        """Construct the list of available GUI bootstraps to display to the user."""
        # Sort the options alphabetically first
        ordered = OrderedDict(sorted(bootstraps.items()))

        # Ensure the first 5 options are: Toga, PySide6, Pygame
        ordered.move_to_end("Pygame", last=False)
        ordered.move_to_end("PySide6", last=False)
        ordered.move_to_end("Toga", last=False)

        # Option None should always be last
        ordered["None"] = None
        ordered.move_to_end("None")

        # Construct the bootstrap options as they should be presented to users.
        # The name of the bootstrap is its registered entry point name. Along with the
        # bootstrap's name, a short message important to a user's choice can be shown
        # also; for instance, several show "does not support iOS/Android deployment".
        bootstrap_choices = {}
        max_len = max(map(len, ordered))
        for name, klass in ordered.items():
            if annotation := getattr(klass, "display_name_annotation", ""):
                annotation = f"{' ' * (max_len - len(name))} ({annotation})"
            bootstrap_choices[f"{name}{annotation or ''}"] = klass

        return bootstrap_choices

    def warn_unused_overrides(self, project_overrides: dict[str, str] | None):
        """Inform user of project configuration overrides that were not used."""
        if project_overrides:
            unused_overrides = "\n    ".join(
                f"{key} = {value}" for key, value in project_overrides.items()
            )
            self.logger.warning()
            self.logger.warning(
                "WARNING: These project configuration overrides were not used:\n\n"
                f"    {unused_overrides}"
            )

    def new_app(
        self,
        template: str | None = None,
        template_branch: str | None = None,
        project_overrides: dict[str, str] | None = None,
        **options,
    ):
        """Ask questions to generate a new application, and generate a stub project from
        the briefcase-template."""
        self.input.prompt()
        self.input.prompt("Let's build a new Briefcase app!")

        context = self.build_context(project_overrides=project_overrides)
        self.prompt_divider()  # close the prompting section of output

        self.warn_unused_overrides(project_overrides)

        self.logger.info(
            f"Generating a new application {context['formal_name']!r}",
            prefix=context["app_name"],
        )

        # Make extra sure we won't clobber an existing application.
        if (self.base_path / context["app_name"]).exists():
            raise BriefcaseCommandError(
                f"A directory named {context['app_name']!r} already exists."
            )

        # Create the project files
        self.generate_template(
            template=(
                template
                if template
                else "https://github.com/beeware/briefcase-template"
            ),
            branch=template_branch,
            output_path=self.base_path,
            extra_context=context,
        )

        self.logger.info(
            f"Generated new application {context['formal_name']!r}",
            prefix=context["app_name"],
        )
        self.logger.info(
            f"""
To run your application, type:

    $ cd {context['app_name']}
    $ briefcase dev

"""
        )

    def verify_tools(self):
        """Verify that the tools needed to run this command exist.

        Raises MissingToolException if a required system tool is missing.
        """
        super().verify_tools()
        Git.verify(tools=self.tools)

    def __call__(
        self,
        template: str | None = None,
        template_branch: str | None = None,
        project_overrides: list[str] = None,
        **options,
    ):
        # Confirm host compatibility, and that all required tools are available.
        # There are no apps, so finalize() will be a no op on app configurations.
        self.finalize()

        return self.new_app(
            template=template,
            template_branch=template_branch,
            project_overrides=parse_project_overrides(project_overrides),
            **options,
        )
