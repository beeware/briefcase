import re
from difflib import SequenceMatcher
from functools import cached_property
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryDirectory
from typing import Callable, Optional
from urllib.parse import urlparse

from packaging.utils import canonicalize_name

from ..config import is_valid_app_name
from .new import NewCommand, titlecase

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import tomli_w

from briefcase.config import make_class_name
from briefcase.exceptions import BriefcaseCommandError


def find_most_similar_path_by_name(paths: list[Path], name: str) -> Path:
    """Given a list of paths and a name, find the path with the most similar name.

    Ties are resolved by selecting the first entry in the paths list.

    :param paths: List of paths to search in
    :param name: Name to compare the path names with
    """
    if not paths:
        raise ValueError("Cannot find most similar path with no paths.")

    max_similarity = float("-inf")

    for path in paths:
        similarity = SequenceMatcher(None, name, path.name).ratio()
        if similarity > max_similarity:
            max_similarity, most_similar = similarity, path

    return most_similar


class ConvertCommand(NewCommand):
    cmd_line = "briefcase convert"
    command = "convert"
    platform = "all"
    output_format = None
    description = "Set up an existing project for Briefcase."

    @cached_property
    def pyproject(self):
        """The contents of the pyproject.toml file (as a dictionary)."""
        if Path("pyproject.toml").exists():
            with open(Path("pyproject.toml"), "rb") as file:
                return tomllib.load(file)
        else:
            return {}

    @cached_property
    def pep621_data(self):
        """The pyproject["project"] dictionary.

        Empty dict if [project] is not in the pyproject.toml file.
        """
        return self.pyproject.get("project", {})

    def create_test_source_dir_validator(self, app_name: str) -> Callable[[str], bool]:
        """Factory for functions that check if the test_source_dir is valid."""

        def validate_test_source_dir(test_source_dir: str) -> bool:
            """Determine if the test_source_dir is valid.

            :param test_source_dir: The candidate test source directory
            :returns: True. If there are any validation problems, raises ValueError with
                  a diagnostic message.
            """
            if not test_source_dir:
                return True

            if not (self.base_path / test_source_dir).is_dir():
                raise ValueError(
                    "The test sources directory must exist and be a directory."
                )
            if (
                test_entry := self.base_path / test_source_dir / f"{app_name}.py"
            ).exists():
                raise ValueError(
                    f"{test_entry} is reserved for the briefcase test entry script, but it already exists.\n"
                    "\n"
                    "Briefcase expects this file to contain the test entry script, so if "
                    f"{self.base_path / test_source_dir} is your test directory, then you must"
                    f"rename {test_entry} before setting up your project for briefcase."
                )

            return True

        return validate_test_source_dir

    def validate_source_dir(self, source_dir: str) -> bool:
        """Determine if the source_dir is valid.

        :param source_dir: The candidate source directory
        :returns: True. If there are any validation problems, raises ValueError with a
            diagnostic message.
        """
        if not (self.base_path / source_dir).is_dir():
            raise ValueError("The source directory must exist and be a directory.")

        if not (self.base_path / source_dir / "__main__.py").is_file():
            raise ValueError(
                f"The source directory ({self.base_path / source_dir}) should contain a ``__main__.py`` file"
            )

        return True

    def input_app_name(self) -> str:
        """Ask about the app name, using hints from the pyproject.toml file or directory
        name if there are any.

        If the name is specified in a PEP621 compliant pyproject.toml file, then it is
        used without prompting.

        :returns: The app name
        """
        intro = (
            "We need a name that can serve as a machine-readable Python package name for\n"
            "your application. This name must be PEP508-compliant - that means the name\n"
            "may only contain letters, numbers, hyphens and underscores; it can't contain\n"
            "spaces or punctuation, and it can't start with a hyphen or underscore."
        )

        if "name" in self.pep621_data and is_valid_app_name(self.pep621_data["name"]):
            return canonicalize_name(self.pep621_data["name"])
        elif is_valid_app_name(Path.cwd().name):  # Directory name is normalised
            default = canonicalize_name(Path.cwd().name)
            intro += (
                "\n"
                f"Based on your PEP508 formatted directory name, we suggest an app name of '{default}',\n"
                "but you can use another name if you want."
            )
        else:
            default = "hello-world"

        return self.input_text(
            intro=intro,
            variable="app name",
            default=default,
            validator=self.validate_app_name,
        )

    def input_formal_name(self, app_name) -> str:
        """Ask about formal name.

        :returns: The source directory
        """
        default = titlecase(" ".join(re.split("[-_]", app_name)))
        return self.input_text(
            intro=(
                "We need a formal name for your application. This is the name that will\n"
                "be displayed to humans whenever the name of the application is displayed. It\n"
                "can have spaces and punctuation if you like, and any capitalization will be\n"
                f"used as you type it. Based on the app name, we believe it is {default}."
            ),
            variable="formal name",
            default=default,
        )

    def get_source_dir_hint(self, module_name: str) -> tuple[str, str]:
        """Parse folder layout to get hint for the source directory.

        :returns: The source directory hint
        :returns: The description text for the source dir prompt.
        """
        valid_src_children = [
            p for p in Path("src").glob("*/") if p.name.isidentifier()
        ]
        valid_root_children = [p for p in Path().glob("*/") if p.name.isidentifier()]

        if Path(f"src/{module_name}").is_dir():
            default = f"src/{module_name}"
        elif Path(module_name).is_dir():
            default = module_name
        elif valid_src_children:
            default = find_most_similar_path_by_name(valid_src_children, module_name)
        else:  # We have already checked that there are directories in the project root
            default = find_most_similar_path_by_name(valid_root_children, module_name)

        intro = (
            "To set up an existing project for Briefcase, we need to know the path of the\n"
            "application entry point relative to the project root (the current working directory).\n"
            "\n"
            "For example, if you have an existing project, myapp, and you can start myapp by\n"
            "running ``src/myapp/__main__.py``, then you should set the source directory to\n"
            "``src/myapp``.\n"
            "\n"
            "Based on your project's folder layout, we believe it might be {default}."
        )
        return default, intro

    def input_source_dir(self, app_name: str) -> str:
        """Ask about the source dir, using hints from the project folder layout.

        :returns: The source directory
        """

        default, intro = self.get_source_dir_hint(app_name)
        return self.input_text(
            intro=intro,
            variable="source directory",
            default=default,
            validator=self.validate_source_dir,
        )

    def input_test_source_dir(self, app_name) -> str:
        """Ask about the test source dir, using hints from the project folder layout.

        :returns: The test source directory
        """
        intro = (
            "We also need to know the path to the test suite (if it exists). The test path\n"
            "should be relative to the project root directory.\n"
            "\n"
            "If the provided directory doesn't exist, it will be created and populated with\n"
            "some default test files."
        )
        if Path("test").exists():
            default = "test"
            intro += (
                "\n\nBased on your project's folder structure, we believe "
                '"test" might be your test directory'
            )
        elif Path("tests").exists():
            default = "tests"
            intro += (
                "\n\nBased on your project's folder structure, we believe "
                + '"tests" might be your test directory'
            )
        else:
            default = "tests"

        return self.input_text(
            intro=intro,
            variable="test source directory",
            default=default,
            validator=self.create_test_source_dir_validator(app_name=app_name),
        )

    def input_description(self) -> str:
        """Ask about the app description, using hints from the pyproject.toml file if
        there are any.

        If the description is specified in a PEP621 compliant pyproject.toml file, then
        it is used without prompting.

        :returns: The app description
        """

        if "description" in self.pep621_data:
            # The description field will be deleted if it is present in the PEP621 data. Moreover, we have no guarantee
            # for the description field being a single line (despite the PEP621 standard mandating it), which can lead
            # to weird exceptions as the cookiecutter template assumes a single-line string. We therefore return an
            # empty line here if a description is in the 621 data beforehand.
            return ""

        return self.input_text(
            intro="Now, we need a one line description for your application.",
            variable="description",
            default="My first application",
        )

    def input_url(self, app_name) -> str:
        """Ask about the URL, using hints from the pyproject.toml file if there are any.

        :returns: The project
        """
        options = list(self.pep621_data.get("urls", {}).values())

        if options is not None and len(options) > 1:
            options.append("Other")
            url = self.input_select(
                intro=(
                    "What is the website URL for this application? If you don't have a website set\n"
                    'up, you can select "Other" and type in a dummy URL.\n'
                    "\n"
                    "We found these urls in the PEP621 formatted pyproject.toml."
                ),
                variable="application URL",
                options=options,
            )

            if url == "Other":
                url = self.input_text(
                    intro="\nWrite the url.",
                    variable="application URL",
                    default=self.make_project_url("com.example", app_name),
                    validator=self.validate_url,
                )
        elif options:
            url = self.input_text(
                intro=(
                    "What is the website URL for this application? If you don't have a website set\n"
                    "up yet, you can put in a dummy URL.\n"
                    "\n"
                    f"We found this url in the PEP621 formatted pyproject.toml: {options[0]}"
                ),
                variable="application URL",
                default=options[0],
                validator=self.validate_url,
            )

        else:
            url = self.input_text(
                intro=(
                    "What is the website URL for this application? If you don't have a website set\n"
                    "up yet, you can put in a dummy URL."
                ),
                variable="application URL",
                default=self.make_project_url("com.example", app_name),
                validator=self.validate_url,
            )

        return url

    def input_bundle(self, url, app_name) -> str:
        if not (url.startswith("https://") or url.startswith("http://")):
            url = f"https://{url}"

        default = ".".join(reversed(urlparse(url).netloc.split(".")))
        return self.input_text(
            (
                "Now we need a bundle identifier for your application. App stores need to\n"
                "protect against having multiple applications with the same name; the bundle\n"
                "identifier is the namespace they use to identify applications that come from\n"
                "you. The bundle identifier is usually the domain name of your company or\n"
                "project, in reverse order.\n"
                "\n"
                "For example, if you are writing an application for Example Corp, whose website\n"
                "is example.com, your bundle would be ``com.example``. The bundle will be\n"
                "combined with your application's machine readable name to form a complete\n"
                f"application identifier (e.g., com.example.{app_name}).\n"
                "\n"
                f"Based on the URL you selected, we believe a reasonable bundle is {default}."
            ),
            variable="bundle identifier",
            default=default,
            validator=self.validate_bundle,
        )

    def input_author(self) -> str:
        """Ask about the author name, using hints from the pyproject.toml file if there
        are any.

        :returns: author name
        """
        intro = (
            "Who do you want to be credited as the author of this application? This could be\n"
            "your own name, or the name of your company you work for."
        )

        options = [
            author["name"]
            for author in self.pep621_data.get("authors", [])
            if "name" in author
        ]

        if not options:
            return self.input_text(
                intro=intro,
                variable="author",
                default="Jane Developer",
            )
        elif len(options) == 1:
            return self.input_text(
                intro=(
                    intro
                    + f"\n\nBased on the PEP621 formatted pyproject.toml file, we believe it might be {options[0]}"
                ),
                variable="author",
                default=options[0],
            )

        # Add a line with all authors joined: E.g. 'Jane Developer & Joe Developer'
        # and a line with Other
        options.append(", ".join(options[:-1]) + f" & {options[-1]}")
        options.append("Other")

        author = self.input_select(
            intro=(
                intro
                + "We found these author names in the PEP621 formatted pyproject.toml. Who do you"
                + "want to be credited as the author of this application?"
            ),
            variable="author",
            options=options,
        )
        if author == "Other":
            author = self.input_text(
                intro="Write the name(s)",
                variable="author",
                default="Jane Developer",
            )

        return author

    def input_email(self, author: str, bundle: str) -> str:
        """Ask about the author email, using hints from the pyproject.toml file if there
        are any.

        :returns: author email
        """
        default = self.make_author_email(author, bundle)
        default_source = "the author name and bundle"
        for author_info in self.pep621_data.get("authors", []):
            if author_info.get("name") == author and author_info.get("email"):
                default = author_info["email"]
                default_source = (
                    "the PEP621 formatted pyproject.toml and your selected author name"
                )

        intro = (
            "What email address should people use to contact the developers of this\n"
            "application? This might be your own email address, or a generic contact address\n"
            f"you set up specifically for this application. Based on {default_source},\n"
            f"we believe it could be {default}."
        )

        author_email = self.input_text(
            intro=intro,
            variable="author's email",
            default=default,
            validator=self.validate_email,
        )

        return author_email

    def get_license_from_text(self, license_text):
        """Infer the license from the license file."""
        hint_patterns = {
            "MIT license": ["Permission is hereby granted, free of charge", "MIT"],
            "Apache Software License": ["Apache"],
            "BSD license": ["Redistribution and use in source and binary forms", "BSD"],
            "GNU General Public License v2 (GPLv2)": [
                "version 2 of the GNU General Public License",
                "GPLv2",
            ],
            "GNU General Public License v2 or later (GPLv2+)": [
                "Free Software Foundation, either version 2 of the License",
                "GPLv2+",
            ],
            "GNU General Public License v3 (GPLv3)": [
                "version 3 of the GNU General Public License",
                "GPLv3",
            ],
            "GNU General Public License v3 or later (GPLv3+)": [
                "either version 3 of the License",
                "GPLv3+",
            ],
        }
        for hint, license_patterns in hint_patterns.items():
            for license_pattern in license_patterns:
                if license_pattern.lower() in license_text.lower():
                    return hint

        return "Other"

    def get_license_hint(self) -> tuple[Optional[str], str]:
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
            with open(self.pep621_data["license"]["file"]) as f:
                license_text = f.read()
            default = self.get_license_from_text(license_text)
            default_source = "the license file"
        elif Path("LICENSE").exists():
            with open("LICENSE") as f:
                license_text = f.read()
            default = self.get_license_from_text(license_text)
            default_source = "the license file"

        if (
            not default
        ):  # Use new if test, not else here since self.get_license_from_text can return None
            return None, intro

        intro += f"\nBased on {default_source} we believe it is {default}."
        return default, intro

    def input_license(self) -> str:
        """Ask about the license, using hints from the pyproject.toml or license file if
        there are any.

        :returns: The project
        """
        default, intro = self.get_license_hint()
        if default:
            project_license = self.input_text(
                intro=intro,
                variable="project license",
                default=default,
            )
        else:
            project_license = self.input_select(
                intro=intro,
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
        return project_license

    def build_app_context(self, project_overrides):
        """Ask the user for details about the app to be created.

        :returns: A context dictionary to be used in the cookiecutter project template.
        """
        app_name = self.input_app_name()
        formal_name = self.input_formal_name(app_name)
        # The class name can be completely derived from the formal name.
        class_name = make_class_name(formal_name)
        # The module name can be completely derived from the app name.
        source_dir = self.input_source_dir(app_name)
        module_name = Path(source_dir).name
        test_source_dir = self.input_test_source_dir(app_name)
        project_name = self.input_project_name(formal_name, override_value=None)
        description = self.input_description()
        url = self.input_url(app_name)
        bundle = self.input_bundle(url, app_name)
        author = self.input_author()
        author_email = self.input_email(author, bundle)
        project_license = self.input_license()

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
        return {"gui_framework": "None"}

    def remove_redundant_fields(self, briefcase_config_file):
        with open(briefcase_config_file, "rb") as f:
            src_config = tomllib.load(f)

        # Remove tags that are in the pyproject.toml file
        briefcase_config = src_config["tool"]["briefcase"]
        app_name = list(briefcase_config["app"])[0]
        app_config = briefcase_config["app"][app_name]
        if self.pep621_data.get("description"):
            del app_config["description"]

        if briefcase_config["url"] == self.pep621_data.get("urls", {}).get("Homepage"):
            del briefcase_config["url"]

        if briefcase_config["license"] == self.get_license_hint()[0]:
            del briefcase_config["license"]

        if "version" in self.pep621_data:
            del briefcase_config["version"]

        # When Briefcase parses PEP621 data, it only considers the first author
        pep621_first_author = next(iter(self.pep621_data.get("authors", [])), {})
        if briefcase_config["author"] == pep621_first_author.get("name"):
            del briefcase_config["author"]
        if briefcase_config["author_email"] == pep621_first_author.get("email"):
            del briefcase_config["author_email"]

        with open(briefcase_config_file, "wb") as f:
            tomli_w.dump(src_config, f)

    def merge_or_copy_pyproject(self, briefcase_config_file) -> None:
        """Merge pyproject.toml file in the src directory with that in dst.

        If the target directory doesn't have a pyproject.toml file, then the newly
        created will be copied

        :param src: The path to the project created by the cookiecutter.
        :param dst: The path where the newly created pyproject.toml file should be
            migrated to.
        """
        pyproject_file = self.base_path / "pyproject.toml"

        self.remove_redundant_fields(briefcase_config_file)

        briefcase_pyproject = briefcase_config_file.read_text()
        if pyproject_file.exists():
            pep621_pyproject = pyproject_file.read_text()

            # The pyproject.toml file in the target directory has no briefcase keys, so it's
            # safe to copy-paste the text, and that way also keep formatting and comments.
            # We merge it this way to preserve comments in the original pyproject.toml file
            briefcase_comment = "# content below this line added by briefcase convert"
            merged_pyproject = (
                f"{pep621_pyproject}\n\n\n{briefcase_comment}\n{briefcase_pyproject}"
            )
        else:
            merged_pyproject = briefcase_pyproject

        with open(pyproject_file, "w") as file:
            file.write(merged_pyproject)

    def migrate_necessary_files(self, project_dir, test_source_dir):
        """Copy and merge the necessary files from project_dir to the current base path.

        Will warn a LICENSE or CHANGELOG file is missing.

        :param project_dir: The path to the project created by the cookiecutter.
        :param test_source_dir: The path to the directory that should contain the test
            entry script
        """
        self.merge_or_copy_pyproject(project_dir / "pyproject.toml")

        # Copy license file if not already there
        license_file = self.pep621_data.get("license", {}).get("file")
        if license_file is not None and Path(license_file).name != "LICENSE":
            self.logger.warning(
                f"License file found in {self.base_path}, but its name is not LICENSE. Renaming the file to LICENSE."
            )
            (self.base_path / license_file).rename(self.base_path / "LICENSE")

            with open(self.base_path / "pyproject.toml") as f:
                pyproject_text = f.read()
            pyproject_text = pyproject_text.replace(license_file, "LICENSE")
            with open(self.base_path / "pyproject.toml", "w") as f:
                f.write(pyproject_text)

        elif not (self.base_path / "LICENSE").exists():
            self.logger.warning(
                f"License file not found in {self.base_path}. Creating a template LICENSE file "
            )
            copy2(project_dir / "LICENSE", self.base_path / "LICENSE")

        # Copy changelog file
        changelog_file = self.base_path / "CHANGELOG"
        if not changelog_file.is_file():
            self.logger.warning(
                f"Changelog file not found in {self.base_path}. You should either create a new changelog file in"
                f" {self.base_path} or rename an already existing changelog file to CHANGELOG."
            )

        # Copy tests or test entry script
        if test_source_dir:
            test_entry_script = project_dir / test_source_dir / f"{project_dir.name}.py"
            copy2(
                test_entry_script,
                self.base_path / test_source_dir / f"{project_dir.name}.py",
            )
        else:
            copytree(project_dir / "tests", self.base_path / "tests")

    def show_welcome_prompt(self) -> None:
        """Show a welcome prompt that describes what this command will do."""
        self.input.prompt()
        self.input.prompt("Let's setup an existing project as a Briefcase app!")

    def convert_app(
        self,
        tmp_path: Path,
        template: Optional[str] = None,
        template_branch: Optional[str] = None,
        **options,
    ) -> None:
        """Run the wizard in a temporary directory and copy the necessary files into the
        project.

        :param tmp_path: Temporary path that should contain the files generated by
            cookiecutter.
        :param template: The cookiecutter template to use.
        :param template_branch: The git branch that the template should use.
        """
        version, template, branch = self.get_version_and_template_info(
            template, template_branch
        )
        context = self.build_context(template, branch, version, project_overrides={})

        self.logger.info()
        self.logger.info(
            f"Generating required files to set up {context['formal_name']!r} with Briefcase"
        )

        # Create the project files
        self.safe_generate_template(
            template=template,
            branch=branch,
            output_path=tmp_path,
            extra_context=context,
            version=version,
        )

        app_path = context["app_name"]
        self.logger.info(
            f"Application '{context['formal_name']}' has been generated. To run your application, type:\n"
            "\n"
            f"cd {app_path}\n"
            "briefcase dev"
        )

        project_dir = tmp_path / context["app_name"]
        self.migrate_necessary_files(project_dir, context["test_source_dir"])

    def validate_pyproject_file(self) -> None:
        """Cannot setup new app if it already has briefcase settings in pyproject."""
        if (self.base_path / "pyproject.toml").exists():
            with open(self.base_path / "pyproject.toml", "rb") as file:
                pyproject = tomllib.load(file)

            if "tool" in pyproject and "briefcase" in pyproject["tool"]:
                raise BriefcaseCommandError(
                    f"[tool.briefcase] already in {self.base_path / 'pyproject.toml'}."
                    " Cannot initialise briefcase for an application that already is packaged with briefcase."
                )

    def validate_not_empty_project(self) -> None:
        """Cannot setup new app for a project containing only a child directory with log
        files or no child directories."""
        # Check first for no child directories
        directories = (p for p in Path().iterdir() if p.is_dir())
        if not (log_dir_candidate := next(directories, None)):
            raise BriefcaseCommandError(
                "Cannot automatically set up briefcase for a project with no directories"
            )

        # If we already failed at setting up this app since it was empty, then there will be a log folder.
        # We still want briefcase to fail so users don't get confused by running the wizard twice and getting
        # different behaviour the second time.
        is_log_dir = log_dir_candidate.is_dir() and all(
            file.suffix == ".log" for file in log_dir_candidate.iterdir()
        )
        if is_log_dir and next(directories, None) is None:
            raise BriefcaseCommandError(
                "Cannot automatically set up briefcase for a project that only contains a log file directory"
            )

    def __call__(
        self,
        template: Optional[str] = None,
        template_branch: Optional[str] = None,
        **options,
    ):
        # Confirm host compatibility, and that all required tools are available.
        # There are no apps, so finalize() will be a no op on app configurations.

        self.finalize()

        self.validate_pyproject_file()
        self.validate_not_empty_project()

        # Setup the app for briefcase
        with TemporaryDirectory() as tmp_path:
            tmp_path = Path(tmp_path)
            self.convert_app(
                tmp_path=tmp_path,
                template=template,
                template_branch=template_branch,
                **options,
            )