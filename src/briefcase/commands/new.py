import re
import subprocess
from email.utils import parseaddr
from typing import Optional
from urllib.parse import urlparse

from cookiecutter import exceptions as cookiecutter_exceptions
import json

from briefcase.config import PEP508_NAME_RE
from briefcase.exceptions import NetworkFailure

from .base import BaseCommand, BriefcaseCommandError
from .create import InvalidTemplateRepository

VALID_BUNDLE_RE = re.compile(r'[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$')


def titlecase(s):
    """
    Convert a string to titlecase.

    Follow Chicago Manual of Style rules for capitalization (roughly).

    * Capitalize *only* the first letter of each word
    * ... unless the word is an acronym (e.g., URL)
    * ... or the word is on the exclude list ('of', 'and', 'the)
    :param s: The input string
    :returns: A capitalized string.
    """
    return ' '.join(
        word if (
            word.isupper()
            or word in {
                'a', 'an', 'and', 'as', 'at', 'but', 'by', 'en', 'for',
                'if', 'in', 'of', 'on', 'or', 'the', 'to', 'via', 'vs'
            }
        ) else word.capitalize()
        for word in s.split(' ')
    )


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

    def distribution_path(self, app):
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
        class_name = re.sub('[^0-9a-zA-Z_]+', '', formal_name)
        if class_name[0].isdigit():
            class_name = '_' + class_name
        return class_name

    def make_app_name(self, formal_name):
        """
        Construct a candidate app name from a formal name.

        :param formal_name: The formal name
        :returns: The candidate app name
        """
        return re.sub('[^0-9a-zA-Z_]+', '', formal_name).lstrip('_').lower()

    def validate_app_name(self, candidate):
        """
        Determine if the app name is valid.

        :param candidate: The candidate name
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        if not PEP508_NAME_RE.match(candidate):
            raise ValueError(
                "App name may only contain letters, numbers, hypens and "
                "underscores, and may not start with a hyphen or underscore."
            )
        if (self.base_path / candidate).exists():
            raise ValueError(
                "A '{candidate}' directory already exists. Select a different "
                "name, move to a different parent directory, or delete the "
                "existing folder.".format(candidate=candidate)
            )

        return True

    def make_module_name(self, formal_name):
        """
        Construct a valid module name from an app name.

        :param formal_name: The app name
        :returns: The app's module name.
        """
        app_name = self.make_app_name(formal_name)
        module_name = app_name.replace('-', '_')
        return module_name

    def validate_bundle(self, candidate):
        """
        Determine if the bundle identifier is valid.

        :param candidate: The candidate bundle identifier
        :returns: True. If there are any validation problems, raises ValueError
            with a diagnostic message.
        """
        if not VALID_BUNDLE_RE.match(candidate):
            raise ValueError(
                "Bundle should be a reversed domain name. It must contain at "
                "least 2 dot-separated sections, and each section may only "
                "include letters, numbers, and hyphens."
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

    def input_text(self, intro, variable, default, validator=None):
        """
        Read a text answer from the user.

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
        if self.input.enabled:
            print(intro or "")
        while True:
            if self.input.enabled:
                print()

            answer = self.input.text_input(
                "{variable} [{default}]: ".format(
                    variable=titlecase(variable),
                    default=default,
                ),
                default=default
            )

            if validator is None:
                return answer

            try:
                validator(answer)
                return answer
            except ValueError as e:
                if not self.input.enabled:
                    raise BriefcaseCommandError(str(e))

                print()
                print("Invalid value; {e}".format(e=e))

    def input_select(self, intro, variable, options):
        """
        Select one from a list of options.

        The first option is assumed to be the default.

        :param intro: An introductory paragraph explaining the question being
            asked.
        :param variable: The variable to display to the user.
        :param options: A list of text strings, describing the available
            options.
        :returns: The string content of the selected option.
        """
        if self.input.enabled:
            print(intro)

        index_choices = [str(key) for key in range(1, len(options) + 1)]
        display_options = '\n'.join(
            "    [{index}] {option}".format(
                index=index, option=option
            )
            for index, option in zip(index_choices, options)
        )
        error_message = "Invalid selection; please enter a number between 1 and {n}".format(
            n=len(options)
        )
        prompt = """
Select one of the following:

{display_options}

{variable} [1]: """.format(
            display_options=display_options,
            variable=titlecase(variable)
        )
        selection = self.input.selection_input(
            prompt=prompt,
            choices=index_choices,
            default="1",
            error_message=error_message
        )
        return options[int(selection) - 1]

    def build_app_context(self, template):
        """
        Ask the user for details about the app to be created.

        :returns: A context dictionary to be used in the cookiecutter project
            template.
        """
        user_args = {}

        with open(template/'cookiecutter.json') as f:
            content = f.read()
        defaults = json.loads(content)

        with open(template/'cookiecutter_context.json') as f:
            content = f.read()
        explanation = json.loads(content)
        # Join JSON multiline arrays into single strings
        for key in explanation:
            explanation[key] = "".join(explanation[key])

        validators = {
            'bundle': self.validate_bundle,
            'author_email': self.validate_email,
            'url': self.validate_url,
        }

        special_cases = {
            'app_name': self.make_app_name,
            'class_name': self.make_class_name,
            'module_name': self.make_module_name,
        }

        for key in defaults:
            if key in special_cases:
                special_case_function = special_cases[key]
                defaults[key] = special_case_function(user_args.get('formal_name'))
            if isinstance(defaults[key], list):
                user_input = self.input_select(
                    intro=explanation.get(key),
                    variable=key,
                    options=defaults.get(key),
                )
            else:
                user_input = self.input_text(
                    intro=explanation.get(key),
                    variable=key,
                    default=defaults.get(key),
                    validator=validators.get(key),
                )

            user_args[key] = user_input

        return user_args

    def new_app(self, template: Optional[str] = None, **options):
        """
        Ask questions to generate a new application, and generate a stub
        project from the briefcase-template.
        """
        if template is None:
            template = 'https://github.com/beeware/briefcase-template'

        cached_template = self.update_cookiecutter_cache(
            template=template,
            branch='v0.3'
        )

        if self.input.enabled:
            print()
            print("Let's build a new Briefcase app!")
            print()

        context = self.build_app_context(template=cached_template)

        print()
        print("Generating a new application '{formal_name}'".format(
            **context
        ))

        # Make extra sure we won't clobber an existing application.
        if (self.base_path / context['app_name']).exists():
            print()
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
                output_dir=str(self.base_path),
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

        print("""
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
