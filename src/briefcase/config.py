from __future__ import annotations

import copy
import keyword
import re
import sys
import unicodedata
from types import SimpleNamespace
from urllib.parse import urlparse

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

from briefcase.platforms import get_output_formats, get_platforms

from .constants import RESERVED_WORDS
from .exceptions import BriefcaseConfigError

# PEP 508 restricts the naming of modules. The PEP defines a regex that uses
# re.IGNORECASE; but in in practice, packaging uses a version that rolls out the lower
# case, which has very slightly different semantics with non-ASCII characters. This
# definition is the one from
# https://github.com/pypa/packaging/blob/24.0/src/packaging/_tokenizer.py#L80
PEP508_NAME_RE = re.compile(r"^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])$")


def is_valid_pep508_name(app_name):
    """Determine if the name is valid by PEP508 rules."""
    return PEP508_NAME_RE.match(app_name)


def is_reserved_keyword(app_name):
    """Determine if the name is a reserved keyword."""
    return keyword.iskeyword(app_name.lower()) or app_name.lower() in RESERVED_WORDS


def is_valid_app_name(app_name):
    return not is_reserved_keyword(app_name) and is_valid_pep508_name(app_name)


def make_class_name(formal_name):
    """Construct a valid class name from a formal name.

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
    xid_continue = xid_start.union(
        {
            "Mn",  # nonspacing marks
            "Mc",  # spacing combining marks
            "Nd",  # decimal number
            "Pc",  # connector punctuations
        }
    )

    # Normalize to NFKC form, then remove any character that isn't
    # in the allowed categories, or is the underscore character;
    # Capitalize the resulting word.
    class_name = "".join(
        ch
        for ch in unicodedata.normalize("NFKC", formal_name)
        if unicodedata.category(ch) in xid_continue or ch in {"_"}
    )

    # If the first character isn't in the 'start' character set,
    # and it isn't already an underscore, prepend an underscore.
    if (
        class_name
        and unicodedata.category(class_name[0]) not in xid_start
        and class_name[0] != "_"
    ):
        class_name = f"_{class_name}"

    return class_name


def validate_url(candidate):
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


def validate_document_type_config(document_type_id, document_type):
    try:
        if not (
            isinstance(document_type["extension"], str)
            and document_type["extension"].isalnum()
        ):
            raise BriefcaseConfigError(
                f"The extension provided for document type {document_type_id!r} is not alphanumeric."
            )
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not provide an extension."
        )

    try:
        if not isinstance(document_type["icon"], str):
            raise BriefcaseConfigError(
                f"The icon definition associated with document type {document_type_id!r} is not a string."
            )
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not define an icon."
        )

    try:
        if not isinstance(document_type["description"], str):
            raise BriefcaseConfigError(
                f"The description associated with document type {document_type_id!r} is not a string."
            )
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not provide a description."
        )

    try:
        validate_url(document_type["url"])
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not provide a URL."
        )
    except ValueError as e:
        raise BriefcaseConfigError(
            f"The URL associated with document type {document_type_id!r} is invalid: {e}"
        )


VALID_BUNDLE_RE = re.compile(r"[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")


def is_valid_bundle_identifier(bundle):
    # Ensure the bundle identifier follows the basi
    if not VALID_BUNDLE_RE.match(bundle):
        return False

    return True


# This is the canonical definition from PEP440, modified to include named groups
PEP440_CANONICAL_VERSION_PATTERN_RE = re.compile(
    r"^((?P<epoch>[1-9][0-9]*)!)?"
    r"(?P<release>(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*)"
    r"((?P<pre_tag>a|b|rc)(?P<pre_value>0|[1-9][0-9]*))?"
    r"(\.post(?P<post>0|[1-9][0-9]*))?"
    r"(\.dev(?P<dev>0|[1-9][0-9]*))?$"
)


def is_pep440_canonical_version(version):
    """Determine if the string describes a valid PEP440 canonical version specifier.

    This implementation comes directly from PEP440 itself.

    :returns: True if the version string is valid; false otherwise.
    """
    return PEP440_CANONICAL_VERSION_PATTERN_RE.match(version) is not None


def parsed_version(version):
    """Return a parsed version string.

    :param version: The parsed version string
    """
    groupdict = PEP440_CANONICAL_VERSION_PATTERN_RE.match(version).groupdict()

    # Convert dot separated string of integers to tuple of integers
    groupdict["release"] = tuple(int(p) for p in groupdict.pop("release").split("."))

    # Convert strings to values
    for key in ("epoch", "pre_value", "post", "dev"):
        try:
            groupdict[key] = int(groupdict[key])
        except TypeError:
            pass

    tag = groupdict.pop("pre_tag")
    value = groupdict.pop("pre_value")
    groupdict["pre"] = (tag, value) if tag is not None else None
    return SimpleNamespace(**groupdict)


class BaseConfig:
    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)


class GlobalConfig(BaseConfig):
    def __init__(
        self,
        project_name,
        version,
        bundle,
        license=None,
        url=None,
        author=None,
        author_email=None,
        requires_python=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.version = version
        self.bundle = bundle
        self.url = url
        self.author = author
        self.author_email = author_email
        self.license = license
        self.requires_python = requires_python

        # Version number is PEP440 compliant:
        if not is_pep440_canonical_version(self.version):
            raise BriefcaseConfigError(
                f"Version number ({self.version}) is not valid.\n\n"
                "Version numbers must be PEP440 compliant; "
                "see https://www.python.org/dev/peps/pep-0440/ for details."
            )

    def __repr__(self):
        return f"<{self.project_name} v{self.version} GlobalConfig>"


class AppConfig(BaseConfig):
    def __init__(
        self,
        app_name,
        version,
        bundle,
        description,
        sources,
        license,
        formal_name=None,
        url=None,
        author=None,
        author_email=None,
        requires=None,
        icon=None,
        document_type=None,
        permission=None,
        template=None,
        template_branch=None,
        test_sources=None,
        test_requires=None,
        supported=True,
        long_description=None,
        console_app=False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # All app configs are created in unfinalized draft form.
        self.__draft__ = True

        self.app_name = app_name
        self.version = version
        self.bundle = bundle
        # Description can only be a single line. Ignore everything else.
        self.description = description.split("\n")[0]
        self.sources = sources
        self.formal_name = app_name if formal_name is None else formal_name
        self.url = url
        self.author = author
        self.author_email = author_email
        self.requires = requires
        self.icon = icon
        self.document_types = {} if document_type is None else document_type
        self.permission = {} if permission is None else permission
        self.template = template
        self.template_branch = template_branch
        self.test_sources = test_sources
        self.test_requires = test_requires
        self.supported = supported
        self.long_description = long_description
        self.license = license
        self.console_app = console_app

        if not is_valid_app_name(self.app_name):
            raise BriefcaseConfigError(
                f"{self.app_name!r} is not a valid app name.\n\n"
                "App names must not be reserved keywords such as 'and', 'for' and 'while'.\n"
                "They must also be PEP508 compliant (i.e., they can only include letters,\n"
                "numbers, '-' and '_'; must start with a letter; and cannot end with '-' or '_')."
            )

        if not is_valid_bundle_identifier(self.bundle):
            raise BriefcaseConfigError(
                f"{self.bundle!r} is not a valid bundle identifier.\n\n"
                "The bundle should be a reversed domain name. It must contain at least 2\n"
                "dot-separated sections; each section may only include letters, numbers,\n"
                "and hyphens; and each section may not contain any reserved words (like\n"
                "'switch', or 'while')."
            )

        for document_type_id, document_type in self.document_types.items():
            validate_document_type_config(document_type_id, document_type)

        # Version number is PEP440 compliant:
        if not is_pep440_canonical_version(self.version):
            raise BriefcaseConfigError(
                f"Version number for {self.app_name!r} ({self.version}) is not valid.\n\n"
                "Version numbers must be PEP440 compliant; "
                "see https://www.python.org/dev/peps/pep-0440/ for details."
            )

        # Sources list doesn't include any duplicates
        source_modules = {source.rsplit("/", 1)[-1] for source in self.sources}
        if len(self.sources) != len(source_modules):
            raise BriefcaseConfigError(
                f"The `sources` list for {self.app_name!r} contains duplicated "
                "package names."
            )

        # There is, at least, a source for the app module
        if self.module_name not in source_modules:
            raise BriefcaseConfigError(
                f"The `sources` list for {self.app_name!r} does not include a "
                f"package named {self.module_name!r}."
            )

    def __repr__(self):
        return f"<{self.bundle_identifier} v{self.version} AppConfig>"

    @property
    def module_name(self):
        """The module name for the app.

        This is derived from the name, but:
        * all `-` have been replaced with `_`.
        """
        return self.app_name.replace("-", "_")

    @property
    def bundle_name(self):
        """The bundle name for the app.

        This is derived from the app name, but:
        * all `_` have been replaced with `-`.
        """
        return self.app_name.replace("_", "-")

    @property
    def bundle_identifier(self):
        """The bundle identifier for the app.

        This is derived from the bundle and the bundle name, joined by a `.`.
        """
        return f"{self.bundle}.{self.bundle_name}"

    @property
    def class_name(self):
        """The class name for the app.

        This is derived from the formal name for the app.
        """
        return make_class_name(self.formal_name)

    @property
    def package_name(self):
        """The bundle name of the app, with `-` replaced with `_` to create something
        that can be used a namespace identifier on Python or Java, similar to
        `module_name`."""
        return self.bundle.replace("-", "_")

    def PYTHONPATH(self, test_mode):
        """The PYTHONPATH modifications needed to run this app.

        :param test_mode: Should test_mode sources be included?
        """
        paths = []
        sources = self.sources
        if test_mode and self.test_sources:
            sources.extend(self.test_sources)

        for source in sources:
            path = "/".join(source.rsplit("/", 1)[:-1])
            if path not in paths:
                paths.append(path)
        return paths

    def main_module(self, test_mode: bool):
        """The path to the main module for the app.

        In normal operation, this is ``app.module_name``; however,
        in test mode, it is prefixed with ``tests.``.

        :param test_mode: Are we running in test mode?
        """
        if test_mode:
            return f"tests.{self.module_name}"
        else:
            return self.module_name


def merge_config(config, data):
    """Merge a new set of configuration requirements into a base configuration.

    :param config: the base configuration to update. This configuration is modified in-
        situ.
    :param data: The new configuration data to merge into the configuration.
    """
    # Properties that are cumulative lists
    for option in [
        "requires",
        "sources",
        "test_requires",
        "test_sources",
    ]:
        value = data.pop(option, [])

        if value:
            config.setdefault(option, []).extend(value)

    # Properties that are cumulative tables
    for option in ["permission"]:
        value = data.pop(option, {})

        if value:
            config.setdefault(option, {}).update(value)

    config.update(data)


def merge_pep621_config(global_config, pep621_config):
    """Merge a PEP621 configuration into a Briefcase configuration."""

    if requires_python := pep621_config.get("requires-python"):
        global_config["requires_python"] = requires_python

    def maybe_update(field, *project_fields):
        # If there's an existing key in the Briefcase config, it takes priority.
        if field in global_config:
            return

        # Traverse the fields in the pep621 config; if the config exists, set it
        # in the Briefcase config.
        datum = pep621_config
        try:
            for key in project_fields:
                datum = datum[key]
        except KeyError:
            pass
        else:
            global_config[field] = datum

    # Keys that map directly
    maybe_update("description", "description")
    maybe_update("license", "license")
    maybe_update("url", "urls", "Homepage")
    maybe_update("version", "version")

    # Use the details of the first author as the Briefcase author.
    if "author" not in global_config:
        try:
            global_config["author"] = pep621_config["authors"][0]["name"]
        except (KeyError, IndexError):
            pass
    if "author_email" not in global_config:
        try:
            global_config["author_email"] = pep621_config["authors"][0]["email"]
        except (KeyError, IndexError):
            pass

    # Briefcase requires is cumulative over PEP621 dependencies
    try:
        pep621_dependencies = pep621_config["dependencies"]
        requires = global_config.get("requires", [])
        global_config["requires"] = pep621_dependencies + requires
    except KeyError:
        pass

    # Briefcase test_requires is cumulative over PEP621 optional test dependencies
    try:
        pep621_test_dependencies = pep621_config["optional-dependencies"]["test"]
        test_requires = global_config.get("test_requires", [])
        global_config["test_requires"] = pep621_test_dependencies + test_requires
    except KeyError:
        pass


def parse_config(config_file, platform, output_format, logger):
    """Parse the briefcase section of the pyproject.toml configuration file.

    This method only does basic structural parsing of the TOML, looking for,
    at a minimum, a ``[tool.briefcase.app.<appname>]`` section declaring the
    existence of a single app. It will also search for:

      * ``[tool.briefcase]`` - global briefcase settings
      * ``[tool.briefcase.app.<appname>]`` - settings specific to the app
      * ``[tool.briefcase.app.<appname>.<platform>]`` - settings specific to
        the platform
      * ``[tool.briefcase.app.<appname>.<platform>.<format>]`` - settings
        specific to the output format

    A configuration can define multiple apps; the final output is the merged
    content of the global, app, platform and output format settings
    for each app, with output format definitions taking precedence over
    platform, over app-level, over global. The final result is a single
    (mostly) flat dictionary for each app.

    :param config_file: A file-like object containing TOML to be parsed.
    :param platform: The platform being targeted
    :param output_format: The output format
    :returns: A dictionary of configuration data. The top level dictionary is
        keyed by the names of the apps that are declared; each value is
        itself the configuration data merged from global, app, platform and
        format definitions.
    """
    try:
        pyproject = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as e:
        raise BriefcaseConfigError(f"Invalid pyproject.toml: {e}") from e

    try:
        global_config = pyproject["tool"]["briefcase"]
    except KeyError as e:
        raise BriefcaseConfigError("No tool.briefcase section in pyproject.toml") from e

    # Merge the PEP621 configuration (if it exists)
    try:
        merge_pep621_config(global_config, pyproject["project"])
    except KeyError:
        pass

    # For consistent results, sort the platforms and formats
    all_platforms = sorted(get_platforms().keys())
    all_formats = sorted(get_output_formats(platform).keys())

    try:
        all_apps = global_config.pop("app")
    except KeyError as e:
        raise BriefcaseConfigError("No Briefcase apps defined in pyproject.toml") from e

    for name, config in [("project", global_config)] + list(all_apps.items()):
        if isinstance(config.get("license"), str):
            section_name = "the Project" if name == "project" else f"{name!r}"
            logger.warning(
                f"""
*************************************************************************
** {f"WARNING: License Definition for {section_name} is Deprecated":67} **
*************************************************************************

    Briefcase now uses PEP 621 format for license definitions.

    Previously, the name of the license was assigned to the 'license'
    field in pyproject.toml. For PEP 621, the name of the license is
    assigned to 'license.text' or the name of the file containing the
    license is assigned to 'license.file'.

    The current configuration for {section_name} has a 'license' field
    that is specified as a string:

        license = "{config['license']}"

    To use the PEP 621 format (and to remove this warning), specify that
    the LICENSE file contains the license for {section_name}:

        license.file = "LICENSE"

*************************************************************************
"""
            )
            config["license"] = {"file": "LICENSE"}

    # Build the flat configuration for each app,
    # based on the requested platform and output format
    app_configs = {}
    for app_name, app_data in all_apps.items():
        # At this point, the base configuration will contain a section
        # for each configured platform. Iterate over all the known platforms,
        # and remove these platform configurations. Keep a copy of the platform
        # configuration if it matches the requested platform, and merge it
        # into the app's configuration
        platform_data = None
        for p in all_platforms:
            try:
                platform_block = app_data.pop(p)

                if p == platform:
                    # If the platform matches the requested format, preserve
                    # it for later use.
                    platform_data = platform_block
                    merge_config(platform_data, platform_data)

                    # The platform configuration will contain a section
                    # for each configured output format. Iterate over all
                    # the output format of the platform, and remove these
                    # output format configurations. Keep a copy of the output
                    # format configuration if it matches the requested output
                    # format, and merge it into the platform's configuration.
                    format_data = None
                    for f in all_formats:
                        try:
                            format_block = platform_data.pop(f)

                            if f == output_format:
                                # If the output format matches the requested
                                # one, preserve it.
                                format_data = format_block

                        except KeyError:
                            pass

                    # If we found a specific configuration for the requested
                    # output format, add it to the platform configuration,
                    # overwriting any platform-level settings with format-level
                    # values.
                    if format_data:
                        merge_config(platform_data, format_data)

            except KeyError:
                pass

        # Now construct the final configuration.
        # First, convert the requirement definition at the global level
        merge_config(global_config, global_config)

        # The app's config starts as a copy of the base briefcase configuration.
        config = copy.deepcopy(global_config)

        # The app name is both the key, and a property of the configuration
        config["app_name"] = app_name

        # Merge the app-specific requirements
        merge_config(config, app_data)

        # If there is platform-specific configuration, merge the requirements,
        # then overwrite the platform-specific values.
        # This will already include any format-specific configuration.
        if platform_data:
            merge_config(config, platform_data)

        # Construct a configuration object, and add it to the list
        # of configurations that are being handled.
        app_configs[app_name] = config

    return global_config, app_configs
