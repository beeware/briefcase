from __future__ import annotations

import re
import sys
from functools import cached_property, partial
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from packaging.utils import canonicalize_name

from ..config import is_valid_app_name
from .new import NewCommand, parse_project_overrides, titlecase

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

from briefcase.config import make_class_name
from briefcase.exceptions import BriefcaseCommandError


class ConvertCommand(NewCommand):
    cmd_line = "briefcase convert"
    command = "convert"
    platform = "all"
    output_format = None
    description = "Set up an existing project for Briefcase."

    @cached_property
    def pyproject(self):
        """The contents of the pyproject.toml file (as a dictionary)."""
        pyproject_file = self.base_path / "pyproject.toml"
        if pyproject_file.exists():
            with open(pyproject_file, "rb") as file:
                return tomllib.load(file)
        else:
            return {}

    @cached_property
    def pep621_data(self):
        """The pyproject["project"] dictionary.

        Empty dict if [project] is not in the pyproject.toml file.
        """
        return self.pyproject.get("project", {})

    def validate_test_source_dir(self, module_name: str, test_source_dir: str) -> bool:
        """Determine if the test_source_dir is valid.

        :param test_source_dir: The candidate test source directory
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
        """
        test_path = self.base_path / test_source_dir
        if (test_entry := test_path / f"{module_name}.py").exists():
            raise ValueError(
                f"'{test_entry}' is reserved for the briefcase test entry script, but it already exists.\n"
                "\n"
                "Briefcase expects this file to contain the test entry script, so if "
                f"'{self.base_path / test_source_dir}' is your test directory, you must "
                f"rename '{test_entry}' before setting up your project for briefcase."
            )

        return True

    def validate_source_dir(self, module_name: str, source_dir: str) -> bool:
        """Determine if the source_dir is valid.

        :param source_dir: The candidate source directory
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
        """
        if (self.base_path / source_dir).name != module_name:
            raise ValueError(
                f"The source directory '{self.base_path / source_dir}' must have "
                f"the same name as the app, but with underscores instead of dashes "
                f"('{module_name}'), not '{(self.base_path / source_dir).name}'."
            )

        if not (self.base_path / source_dir).is_dir():
            raise ValueError(
                "The source directory must exist and contain a '__main__.py' file."
            )

        if not (self.base_path / source_dir / "__main__.py").is_file():
            raise ValueError("The source directory must contain a '__main__.py' file")

        return True

    def _validate_existing_app_name(self, candidate):
        """Override default validation to allow app names with a pre-existing
        directory."""
        pass

    def input_app_name(self, override_value: str | None) -> str:
        """Ask about the app name, using hints from the pyproject.toml file or directory
        name if there are any.

        If the name is specified in a PEP621 compliant pyproject.toml file, then it is
        used without prompting.

        :returns: The app name
        """
        intro = (
            "We need a name that can serve as a machine-readable Python package name for "
            "your application. This name must be PEP508-compliant - that means the name "
            "may only contain letters, numbers, hyphens and underscores; it can't contain "
            "spaces or punctuation, and it can't start with a hyphen or underscore."
        )

        default = "hello-world"
        if (
            "name" in self.pep621_data
            and is_valid_app_name(self.pep621_data["name"])
            and override_value is None
        ):
            app_name = canonicalize_name(self.pep621_data["name"])
            self.prompt_divider(title="App name")
            self.input.prompt()
            self.input.prompt(
                f"Using value from PEP621 formatted pyproject.toml {app_name!r}"
            )
            return app_name

        if is_valid_app_name(self.base_path.name):  # Directory name is normalised
            default = canonicalize_name(self.base_path.name)
            intro += (
                "\n\n"
                f"Based on your PEP508 formatted directory name, we suggest an "
                f"app name of '{default}', but you can use another name if you want."
            )

        return self.input_text(
            intro=intro,
            variable="app name",
            default=default,
            validator=self.validate_app_name,
            override_value=override_value,
        )

    def input_formal_name(self, app_name: str, override_value: str | None) -> str:
        """Ask about formal name.

        :returns: The source directory
        """
        default = titlecase(" ".join(re.split("[-_]", app_name)))
        return self.input_text(
            intro=(
                "We need a formal name for your application. This is the name that "
                "will be displayed to humans whenever the name of the application is "
                "displayed. It can include spaces and punctuation, and any "
                "capitalization will be used as you type it here.\n"
                "\n"
                f"Based on the app name, we suggest a formal name of '{default}', but "
                "you can use another name if you want."
            ),
            variable="formal name",
            default=default,
            override_value=override_value,
        )

    def get_source_dir_hint(self, app_name: str, module_name: str) -> tuple[str, str]:
        """Parse folder layout to get hint for the source directory.

        :returns: The source directory hint
        :returns: The description text for the source dir prompt.
        """
        possible_src_dirs = [
            p.parent for p in self.base_path.glob(f"**/{module_name}/__main__.py")
        ]
        if (self.base_path / f"src/{module_name}") in possible_src_dirs:
            default = self.base_path / f"src/{module_name}"
        elif (self.base_path / module_name) in possible_src_dirs:
            default = self.base_path / module_name
        elif possible_src_dirs:
            default = min(
                possible_src_dirs,
                key=lambda p: (len(p.parents), len(str(p))),
            )
        else:  # We have already checked that there are directories in the project root
            raise BriefcaseCommandError(
                "Cannot find a suitable source directory for the app.\n"
                "\n"
                f"Based on your app name, '{app_name}', you must have a directory "
                f"named '{module_name}', either in your project root or a subdirectory "
                f"(e.g. 'src/{module_name}'), that contains a '__main__.py'."
            )

        default = str(default.relative_to(self.base_path)).replace("\\", "/")
        intro = (
            "To set up an existing project for Briefcase, we need to know the path "
            "of the application entry point relative to the project root (the current "
            "working directory).\n"
            "\n"
            "For example, if you have an existing project 'myapp', and you can start "
            "'myapp' by running 'src/myapp/__main__.py', then you should set the source "
            "directory to 'src/myapp'.\n"
            "\n"
            f"Based on your project's folder layout, we believe it might be '{default}'."
        )
        return default, intro

    def input_source_dir(
        self,
        app_name: str,
        module_name: str,
        override_value: str | None,
    ) -> str:
        """Ask about the source dir, using hints from the project folder layout.

        :returns: The source directory
        """
        default, intro = self.get_source_dir_hint(app_name, module_name)
        return self.input_text(
            intro=intro,
            variable="source directory",
            default=default,
            validator=partial(self.validate_source_dir, module_name),
            override_value=override_value,
        )

    def input_test_source_dir(self, module_name, override_value) -> str:
        """Ask about the test source dir, using hints from the project folder layout.

        :returns: The test source directory
        """
        intro = (
            "We also need to know the path to the test suite (if it exists). The test path "
            "should be relative to the project root directory.\n"
            "\n"
            "If the provided directory doesn't exist, it will be created and populated with "
            "some default test files."
        )
        if (self.base_path / "tests").is_dir():
            default = "tests"
            intro += (
                "\n\nBased on your project's folder structure, we believe "
                + "'tests' might be your test directory"
            )
        elif (self.base_path / "test").is_dir():
            default = "test"
            intro += (
                "\n\nBased on your project's folder structure, we believe "
                "'test' might be your test directory"
            )
        else:
            default = "tests"

        return self.input_text(
            intro=intro,
            variable="test source directory",
            default=default,
            validator=partial(self.validate_test_source_dir, module_name),
            override_value=override_value,
        )

    def input_description(self, override_value: str | None) -> str:
        """Ask about the app description, using hints from the pyproject.toml file if
        there are any.

        If the description is specified in a PEP621 compliant pyproject.toml file, then
        it is used without prompting.

        :returns: The app description
        """
        if "description" in self.pep621_data and override_value is None:
            description = self.pep621_data["description"]

            self.prompt_divider(title="Description")
            self.input.prompt()
            self.input.prompt(
                f"Using value from PEP621 formatted pyproject.toml {description!r}"
            )
            return description

        return self.input_text(
            intro="Now, we need a one line description for your application.",
            variable="description",
            default="My first application",
            override_value=override_value,
        )

    def input_url(self, app_name, override_value: str | None) -> str:
        """Ask about the URL, using hints from the pyproject.toml file if there are any.

        :returns: The project
        """
        options = list(self.pep621_data.get("urls", {}).values())

        if not options or override_value:
            default = self.make_project_url("com.example", app_name)
            return self.input_text(
                intro=(
                    "What website URL do you want to use for this application? Based "
                    f"on your existing 'pyproject.toml', this might be {default}"
                ),
                variable="application URL",
                default=default,
                validator=self.validate_url,
                override_value=override_value,
            )

        options.append("Other")
        url = self.select_option(
            intro=(
                "What website URL do you want to use for this application? The "
                "following URLs are defined in your existing 'pyproject.toml'; "
                "select 'Other' to provide a different URL."
            ),
            variable="application URL",
            default=None,
            options=options,
            override_value=override_value,
        )

        if url == "Other":
            url = self.input_text(
                intro="What website URL do you want to use for the application?",
                variable="application URL",
                default=self.make_project_url("com.example", app_name),
                validator=self.validate_url,
            )

        return url

    def input_bundle(self, url, app_name, override_value: str | None) -> str:
        default = ".".join(reversed(urlparse(url).netloc.split(".")))
        return self.input_text(
            intro=(
                "Now we need a bundle identifier for your application.\n"
                "\n"
                "App stores need to protect against having multiple applications with "
                "the same name; the bundle identifier is the namespace they use to "
                "identify applications that come from you. The bundle identifier is "
                "usually the domain name of your company or project, in reverse "
                "order.\n"
                "\n"
                "Based on the application URL you selected, it looks like your bundle "
                f"should be '{default}'. The bundle will be combined with your "
                "application's machine readable name to form a complete application "
                f"identifier ('{default}.{app_name}')."
            ),
            variable="bundle identifier",
            default=default,
            validator=self.validate_bundle,
            override_value=override_value,
        )

    def input_author(self, override_value: str | None) -> str:
        """Ask about the author name, using hints from the pyproject.toml file if there
        are any.

        :returns: author name
        """
        intro = (
            "Who do you want to be credited as the author of this application? "
            "This could be your own name, or the name of your company you work for."
        )

        options = [
            author["name"]
            for author in self.pep621_data.get("authors", [])
            if "name" in author
        ]

        if not options or override_value is not None:
            return self.input_text(
                intro=intro,
                variable="author",
                default="Jane Developer",
                override_value=override_value,
            )
        elif len(options) > 1:
            # Add a line with all authors joined: E.g. 'Jane Developer & Joe Developer'
            # and a line with Other
            options.append(", ".join(options[:-1]) + f" & {options[-1]}")

        options.append("Other")

        # We want to use the input_text-function if override_value is provided or if the selected author is "Other"
        # However, since we don't want the select_option prompt if an override value is provided, we need to
        # initialise the author variable here.
        author = self.select_option(
            intro=(
                intro
                + "\n\n"
                + "We found these author names in the PEP621 formatted "
                + "'pyproject.toml'. Who do you want to be credited as the author of "
                + "this application?"
            ),
            variable="Author",
            options=options,
            default=None,
            override_value=None,
        )
        if author == "Other":
            author = self.input_text(
                intro="Who do you want to be credited as the author of this application?",
                variable="author",
                default="Jane Developer",
                override_value=None,
            )

        return author

    def input_email(self, author: str, bundle: str, override_value: str | None) -> str:
        """Ask about the author email, using hints from the pyproject.toml file if there
        are any.

        :returns: author email
        """
        default = self.make_author_email(author, bundle)
        default_source = "the author name and bundle"
        for author_info in self.pep621_data.get("authors", []):
            if author_info.get("name") == author and author_info.get("email"):
                default = author_info["email"]
                default_source = "the selected author name"

        intro = (
            "What email address should people use to contact the developers of this "
            "application? This might be your own email address, or a generic contact address "
            f"you set up specifically for this application. Based on {default_source}, "
            f"we believe it could be '{default}'."
        )

        author_email = self.input_text(
            intro=intro,
            variable="author's email",
            default=default,
            validator=self.validate_email,
            override_value=override_value,
        )

        return author_email

    def get_license_from_text(self, license_text: str) -> str:
        """Infer the license from the license file."""
        # The order here is quite important. If we have GPLvX+ after GPLvX, then it will
        # never be matched if the license text is GPLvX+, since it will already have
        # matched GPLvX. We search for MIT last, because words like PERMITTED and
        # LIMITED will generate a false match.

        hint_patterns = {
            "Apache Software License": ["Apache"],
            "BSD license": [
                "Redistribution and use in source and binary forms",
                "BSD",
            ],
            "GNU General Public License v2 or later (GPLv2+)": [
                "Free Software Foundation, either version 2 of the License",
                "GPLv2+",
            ],
            "GNU General Public License v2 (GPLv2)": [
                "version 2 of the GNU General Public License",
                "GPLv2",
            ],
            "GNU General Public License v3 or later (GPLv3+)": [
                "either version 3 of the License",
                "GPLv3+",
            ],
            "GNU General Public License v3 (GPLv3)": [
                "version 3 of the GNU General Public License",
                "GPLv3",
            ],
            "MIT license": [
                "Permission is hereby granted, free of charge",
                "MIT",
            ],
        }
        for hint, license_patterns in hint_patterns.items():
            for license_pattern in license_patterns:
                if license_pattern.lower() in license_text.lower():
                    return hint

        return "Other"

    def get_license_hint(self) -> tuple[str | None, str]:
        """Get hint for project license, either by reading pyproject.toml or the license
        file.

        :returns: The default value of the license - None if we cannot infer a license.
        :returns: The intro text to use when prompting the license
        """
        intro = "What license do you want to use for this project's code? "
        default = None

        # If there is license information in the pyproject.toml file, use that, otherwise check the license file
        if "text" in self.pep621_data.get("license", {}):
            default = self.get_license_from_text(self.pep621_data["license"]["text"])
            default_source = "the PEP621 formatted pyproject.toml"
        elif "file" in self.pep621_data.get("license", {}):
            license_text = (
                self.base_path / self.pep621_data["license"]["file"]
            ).read_text(encoding="utf-8")
            default = self.get_license_from_text(license_text)
            default_source = "the license file"
        elif (self.base_path / "LICENSE").exists():
            license_text = (self.base_path / "LICENSE").read_text(encoding="utf-8")
            default = self.get_license_from_text(license_text)
            default_source = "the license file"
        elif (self.base_path / "LICENCE").exists():
            license_text = (self.base_path / "LICENCE").read_text(encoding="utf-8")
            default = self.get_license_from_text(license_text)
            default_source = "the license file"
        else:
            return None, intro

        intro += f"\nBased on {default_source} we believe it is {default!r}."
        return default, intro

    def input_license(self, override_value: str | None) -> str:
        """Ask about the license, using hints from the pyproject.toml or license file if
        there are any.

        :returns: The project
        """
        default, intro = self.get_license_hint()
        options = [
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
            intro=intro,
            variable="Project License",
            options=options,
            default=default,
            override_value=override_value,
        )

    def build_app_context(self, project_overrides):
        """Ask the user for details about the app to be created.

        :returns: A context dictionary to be used in the cookiecutter project template.
        """
        app_name = self.input_app_name(
            override_value=project_overrides.pop("app_name", None)
        )
        formal_name = self.input_formal_name(
            app_name, override_value=project_overrides.pop("formal_name", None)
        )
        # The class name can be completely derived from the formal name.
        class_name = make_class_name(formal_name)
        # The module name can be completely derived from the app name.
        module_name = self.make_module_name(app_name)
        source_dir = self.input_source_dir(
            app_name,
            module_name,
            override_value=project_overrides.pop("source_dir", None),
        )
        test_source_dir = self.input_test_source_dir(
            module_name, override_value=project_overrides.pop("test_source_dir", None)
        )
        project_name = self.input_project_name(
            formal_name, override_value=project_overrides.pop("project_name", None)
        )
        description = self.input_description(
            override_value=project_overrides.pop("description", None)
        )
        url = self.input_url(app_name, project_overrides.pop("url", None))
        bundle = self.input_bundle(url, app_name, project_overrides.pop("bundle", None))
        author = self.input_author(override_value=project_overrides.pop("author", None))
        author_email = self.input_email(
            author, bundle, override_value=project_overrides.pop("author_email", None)
        )
        project_license = self.input_license(
            override_value=project_overrides.pop("license", None)
        )

        return {
            "formal_name": formal_name,
            "app_name": app_name,
            "class_name": class_name,
            "module_name": module_name,
            "project_name": project_name,
            "source_dir": source_dir,
            "test_source_dir": test_source_dir,
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
        # We must set the GUI-framework to None here since the convert-command uses the new-command
        # template. This template includes dependencies for the GUI-frameworks. However, if a project
        # already is set up for a GUI-framework, then those dependencies should already be listed.
        # To prevent the same dependency being listed twice (once in the PEP621-section and once in the
        # briefcase-section), possibly with different versions, we set the GUI-framework to None here.
        return {"gui_framework": "None"}

    def merge_or_copy_pyproject(self, briefcase_config_file: Path) -> None:
        """Merge pyproject.toml file made by the cookiecutter with the one in the
        existing project.

        If the target directory doesn't have a pyproject.toml file, then the newly
        created will be copied

        :param briefcase_config_file: The path to the project created by the
            cookiecutter.
        """
        pyproject_file = self.base_path / "pyproject.toml"

        briefcase_pyproject = briefcase_config_file.read_text(encoding="utf-8")
        if pyproject_file.exists():
            pep621_pyproject = pyproject_file.read_text(encoding="utf-8")

            # The pyproject.toml file in the target directory has no briefcase keys, so it's
            # safe to copy-paste the text, and that way also keep formatting and comments.
            # We merge it this way to preserve comments in the original pyproject.toml file
            briefcase_comment = "# content below this line added by briefcase convert"
            merged_pyproject = (
                f"{pep621_pyproject}\n\n\n{briefcase_comment}\n{briefcase_pyproject}"
            )
        else:
            merged_pyproject = briefcase_pyproject

        with open(pyproject_file, "w", encoding="utf-8") as file:
            file.write(merged_pyproject)

    def migrate_necessary_files(self, project_dir, test_source_dir, module_name):
        """Copy and merge the necessary files from project_dir to the current base path.

        Will warn a LICENSE or CHANGELOG file is missing.

        :param project_dir: The path to the project created by the cookiecutter.
        :param test_source_dir: The path to the directory that should contain the test
            entry script
        """
        self.merge_or_copy_pyproject(project_dir / "pyproject.toml")

        # Copy license file if not already there
        license_file = self.pep621_data.get("license", {}).get("file")

        if license_file is None and not (self.base_path / "LICENSE").exists():
            self.logger.warning(
                f"\nLicense file not found in '{self.base_path}'. "
                "Briefcase will create a template 'LICENSE' file."
            )
            copy2(project_dir / "LICENSE", self.base_path / "LICENSE")

        # Copy changelog file
        changelog_file = self.base_path / "CHANGELOG"
        if not changelog_file.is_file():
            self.logger.warning(
                f"\nChangelog file not found in '{self.base_path}'. You should either "
                f"create a new '{self.base_path / 'CHANGELOG'}' file, or rename an "
                "already existing changelog file to 'CHANGELOG'."
            )

        # Copy tests or test entry script
        test_path = self.base_path / test_source_dir
        if test_path.exists():
            test_entry_script = project_dir / test_source_dir / f"{module_name}.py"
            copy2(
                test_entry_script,
                test_path / f"{module_name}.py",
            )
        else:
            copytree(project_dir / test_source_dir, test_path)

    def convert_app(
        self,
        tmp_path: Path,
        template: str | None = None,
        template_branch: str | None = None,
        project_overrides: dict[str, str] | None = None,
        **options,
    ) -> None:
        """Run the wizard in a temporary directory and copy the necessary files into the
        project.

        :param tmp_path: Temporary path that should contain the files generated by
            cookiecutter.
        :param template: The cookiecutter template to use.
        :param template_branch: The git branch that the template should use.
        """
        self.input.prompt()
        self.input.prompt("Let's setup an existing project as a Briefcase app!")
        context = self.build_context(project_overrides)
        self.prompt_divider()  # close the prompting section of output

        self.warn_unused_overrides(project_overrides)

        self.logger.info()
        self.logger.info(
            f"Generating required files to set up '{context['formal_name']}' with Briefcase",
            prefix=context["app_name"],
        )

        # Create the project files
        self.generate_template(
            template=(
                template
                if template
                else "https://github.com/beeware/briefcase-template"
            ),
            branch=template_branch,
            output_path=tmp_path,
            extra_context=context,
        )

        project_dir = tmp_path / context["app_name"]
        self.migrate_necessary_files(
            project_dir, context["test_source_dir"], context["module_name"]
        )

        self.logger.info(
            f"Converted existing application '{context['formal_name']}'",
            prefix=context["app_name"],
        )
        self.logger.info(
            """
To run your application, type:

    $ briefcase dev

"""
        )

    def validate_pyproject_file(self) -> None:
        """Cannot setup new app if it already has briefcase settings in pyproject."""
        if not (self.base_path / "pyproject.toml").exists():
            raise BriefcaseCommandError(
                "Cannot automatically set up Briefcase for a project without a "
                "'pyproject.toml' file."
            )

        with open(self.base_path / "pyproject.toml", "rb") as file:
            pyproject = tomllib.load(file)

        if "tool" in pyproject and "briefcase" in pyproject["tool"]:
            raise BriefcaseCommandError(
                "Your 'pyproject.toml' file already contains a Briefcase configuration."
            )

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

        self.validate_pyproject_file()

        # Setup the app for briefcase
        with TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            self.convert_app(
                tmp_path=tmp_path,
                template=template,
                template_branch=template_branch,
                project_overrides=parse_project_overrides(project_overrides),
                **options,
            )
