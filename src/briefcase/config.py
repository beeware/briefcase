from __future__ import annotations

import copy
import keyword
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from packaging.licenses import InvalidLicenseExpression, canonicalize_license_expression
from packaging.version import InvalidVersion, Version

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

from briefcase.debuggers.base import BaseDebugger
from briefcase.platforms import get_output_formats, get_platforms

from .constants import MIME_TYPE_REGISTRIES, RESERVED_WORDS
from .exceptions import BriefcaseConfigError, InvalidVersionError

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
            "Pc",  # connector punctuation
        }
    )

    # Normalize to NFKC form, then remove any character that isn't
    # in the allowed categories, or is the underscore character;
    # Capitalize the resulting word.
    class_name = "".join(
        ch
        for ch in unicodedata.normalize("NFKC", formal_name)
        if unicodedata.category(ch) in xid_continue or ch == "_"
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


def validate_document_type_config(app_name, document_type_id, document_type):
    try:
        if not (
            isinstance(document_type["extension"], str)
            and document_type["extension"].isalnum()
        ):
            raise BriefcaseConfigError(
                f"The extension provided for document type "
                f"{document_type_id!r} is not alphanumeric."
            )
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not provide an extension."
        ) from None

    try:
        if not isinstance(document_type["icon"], str):
            raise BriefcaseConfigError(
                f"The icon definition associated with document type "
                f"{document_type_id!r} is not a string."
            )
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not define an icon."
        ) from None

    try:
        if not isinstance(document_type["description"], str):
            raise BriefcaseConfigError(
                f"The description associated with document type "
                f"{document_type_id!r} is not a string."
            )
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not provide a description."
        ) from None

    try:
        validate_url(document_type["url"])
    except KeyError:
        raise BriefcaseConfigError(
            f"Document type {document_type_id!r} does not provide a URL."
        ) from None
    except ValueError as e:
        raise BriefcaseConfigError(
            f"The URL associated with document type {document_type_id!r} "
            f"is invalid: {e}"
        ) from None

    try:
        mime_type = document_type["mime_type"]
        if not isinstance(mime_type, str):
            raise BriefcaseConfigError(
                f"The MIME type associated with document type "
                f"{document_type_id!r} is not a string."
            )
        try:
            registry, _ = mime_type.split("/")
            if registry not in MIME_TYPE_REGISTRIES:
                raise BriefcaseConfigError(
                    f"The MIME type {mime_type!r} for document type "
                    f"{document_type_id!r} uses an invalid registry {registry!r}."
                )
        except ValueError:
            raise BriefcaseConfigError(
                f"The MIME type {mime_type!r} for document type "
                f"{document_type_id!r} is not in 'type/subtype' format."
            ) from None
    except KeyError:
        # mime_type is optional; if it's not provided, use a default.
        document_type["mime_type"] = f"application/x-{app_name}-{document_type_id}"

    if sys.platform == "darwin":  # pragma: no-cover-if-not-macos
        from briefcase.platforms.macOS.utils import is_uti_core_type, mime_type_to_uti

        macOS = document_type.setdefault("macOS", {})
        content_types = macOS.get("LSItemContentTypes", None)
        mime_type = document_type.get("mime_type", None)

        if isinstance(content_types, list):
            if len(content_types) > 1:
                raise BriefcaseConfigError(
                    f"""\
Document type {document_type_id!r} has multiple content types. Specifying
multiple values in a LSItemContentTypes key is only valid when multiple document
types are manually grouped together in the Info.plist file. For Briefcase apps,
document types are always separately declared in the configuration file, so only
a single value should be provided.
                """
                )

            macOS["LSItemContentTypes"] = content_types
            uti = content_types[0]
        elif isinstance(content_types, str):
            # If the content type is a string, convert it to a list
            macOS["LSItemContentTypes"] = [content_types]
            uti = content_types
        else:
            uti = None

        # If an UTI is provided in LSItemContentTypes,
        # that takes precedence over a MIME type
        if is_uti_core_type(uti) or ((uti := mime_type_to_uti(mime_type)) is not None):
            macOS.setdefault("is_core_type", True)
            macOS.setdefault("LSItemContentTypes", [uti])
            macOS.setdefault("LSHandlerRank", "Alternate")
        else:
            # LSItemContentTypes will default to bundle.app_name.document_type_id
            # in the Info.plist template if it is not provided.
            macOS.setdefault("is_core_type", False)
            macOS.setdefault("LSHandlerRank", "Owner")
            macOS.setdefault("UTTypeConformsTo", ["public.data", "public.content"])

        macOS.setdefault("CFBundleTypeRole", "Viewer")
    else:  # pragma: no-cover-if-is-macos
        pass


def validate_install_options_config(config, opt_type, **others):
    """Validate that install/uninstall options are valid and complete, and convert to a
    dict.

    The dict format is required because Cookiecutter doesn't allow passing a list as a
    context value; you have to use the reliable iteration order of a dict instead.

    :param config: The table form of options
    :param opt_type: The label of the option type being parsed ("install" or
        "uninstall")
    :param others: A dictionary of other parsed option types. The keys are
        the option types, and the values are the dictionary of parse options. Options
        in `config` must be unique against these keys.
    """
    options = {}
    known_names = set()
    if config:
        for i, config_item in enumerate(config):
            try:
                name = config_item["name"]
                if not isinstance(name, str):
                    raise BriefcaseConfigError(
                        f"Name for {opt_type} option {i} is not a string."
                    )
            except KeyError:
                raise BriefcaseConfigError(
                    f"{opt_type.title()} option {i} does not define a `name`."
                ) from None

            # Options must be valid Python identifiers
            if not name.isidentifier():
                raise BriefcaseConfigError(
                    f"{name!r} cannot be used as an {opt_type} option name, "
                    "as it is not a valid Python identifier."
                )

            # Option names may be coerced into upper case; and there are
            # a small number of reserved identifiers.
            if name.upper() == "ALLUSERS":
                raise BriefcaseConfigError(
                    f"{name!r} is a reserved {opt_type} option identifier."
                )

            option = {}
            if name.upper() in known_names:
                raise BriefcaseConfigError(
                    f"{opt_type.title()} option names must be unique. The name "
                    f"{name!r}, used by {opt_type} option {i}, has already "
                    "been defined."
                )
            else:
                for other_type, other_options in others.items():
                    if name.upper() in {n.upper() for n in other_options}:
                        raise BriefcaseConfigError(
                            f"{opt_type.title()} option names must be unique. The name "
                            f"{name!r} is already used as an {other_type} option."
                        )

            # options needs to retain the original name, but we need names to be
            # case-unique as well, so we track a separate set of known upper case names.
            known_names.add(name.upper())
            options[name] = option

            try:
                # Options must have a string title.
                option["title"] = config_item["title"]
                if not isinstance(option["title"], str):
                    raise BriefcaseConfigError(
                        f"Title for {opt_type} option {name!r} is not a string."
                    )
            except KeyError:
                raise BriefcaseConfigError(
                    f"{opt_type.title()} option {name!r} does not provide a title."
                ) from None

            try:
                # Options must have a string title.
                option["description"] = config_item["description"]
                if not isinstance(option["description"], str):
                    raise BriefcaseConfigError(
                        f"Description for {opt_type} option {name!r} is not a string."
                    )
            except KeyError:
                raise BriefcaseConfigError(
                    f"{opt_type.title()} option {name!r} does not provide "
                    "a description."
                ) from None

            # Options are booleans, and are False by default
            option["default"] = bool(config_item.get("default", False))

    return options


VALID_BUNDLE_RE = re.compile(r"[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")


def is_valid_bundle_identifier(bundle):
    """Check if the bundle identifier follows the basic reversed domain name pattern."""
    return VALID_BUNDLE_RE.match(bundle) is not None


def parse_boolean(value: str) -> bool:
    """Takes a string value and attempts to convert to a boolean value."""

    truth_vals = {"true", "t", "yes", "y", "1", "on"}
    false_vals = {"false", "f", "no", "n", "0", "off"}

    normalised_val = value.strip().lower()

    if normalised_val in truth_vals:
        return True
    elif normalised_val in false_vals:
        return False
    else:
        raise ValueError(
            f"Invalid boolean value: {value!r}. "
            f"Expected one of {truth_vals | false_vals}"
        )


class BaseConfig:
    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def update(self, data):
        """Add fields and values from data to BaseConfig instance.

        Any existing fields named in data will be overwritten. To merge
        data with existing configs, use the `merge_config` function.

        :param data: The new configuration data dictionary.
        """
        for key, configs in data.items():
            setattr(self, key, configs)

    def copy(self):
        return type(self)(**self.__dict__)

    def setdefault(self, field_name, default_value):
        """Return the field_name field or, if it does not exist, create it to hold
        default_value.

        Behaves similarly to dict.setdefault().

        :param field_name: The name of the desired/new field.
        :param default_value: The value to assign to self.field_name if it does not
            already exist.
        """
        if not hasattr(self, field_name):
            setattr(self, field_name, default_value)

        return getattr(self, field_name)


class GlobalConfig(BaseConfig):
    def __init__(
        self,
        project_name,
        version,
        bundle,
        license=None,
        license_files=None,
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
        self.license_files = [] if license_files is None else license_files
        self.requires_python = requires_python

        # Version number is compliant with PEP440 (and related updates):
        try:
            # If input is already a version object (can happen by copying), use as-is
            if isinstance(version, Version):
                self.version = version
            else:
                self.version = Version(version)
        except (InvalidVersion, TypeError):
            raise InvalidVersionError(
                f"Version number ({self.version}) is not valid."
            ) from None

    def __repr__(self):
        return f"<{self.project_name} v{self.version} GlobalConfig>"


class AppConfig(BaseConfig):
    def __init__(
        self,
        app_name,
        version,
        bundle,
        description,
        license=None,
        license_files=None,
        sources=None,
        formal_name=None,
        url=None,
        author=None,
        author_email=None,
        requires=None,
        icon=None,
        document_type=None,
        install_option=None,
        uninstall_option=None,
        permission=None,
        template=None,
        template_branch=None,
        test_sources=None,
        test_requires=None,
        supported=True,
        long_description=None,
        console_app=False,
        requirement_installer_args: list[str] | None = None,
        external_package_path: str | None = None,
        external_package_executable_path: str | None = None,
        install_launcher: bool | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.app_name = app_name
        self.version = version
        self.bundle = bundle.lower()
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
        self.license_files = [] if license_files is None else license_files
        self.console_app = console_app
        self.requirement_installer_args = (
            [] if requirement_installer_args is None else requirement_installer_args
        )
        self.external_package_path = external_package_path
        self.external_package_executable_path = external_package_executable_path
        self.install_launcher = (
            install_launcher if (install_launcher is not None) else (not console_app)
        )

        self.test_mode: bool = False

        self.debugger: BaseDebugger | None = None
        self.debugger_host: str | None = None
        self.debugger_port: int | None = None

        if not is_valid_app_name(self.app_name):
            raise BriefcaseConfigError(
                f"{self.app_name!r} is not a valid app name."
                f"\n\n"
                "App names must not be reserved keywords such as 'and', 'for' and "
                "'while'. They must also be PEP508 compliant (i.e., they can only "
                "include letters, numbers, '-' and '_'; must start with a letter; "
                "and cannot end with '-' or '_')."
            )

        if not is_valid_bundle_identifier(self.bundle):
            raise BriefcaseConfigError(
                f"{self.bundle!r} is not a valid bundle identifier."
                f"\n\n"
                "The bundle should be a reversed domain name. It must contain at least "
                "2 dot-separated sections; each section may only include letters, "
                "numbers, and hyphens; and each section may not contain any reserved "
                "words (like 'switch', or 'while')."
            )

        for document_type_id, document_type in self.document_types.items():
            validate_document_type_config(
                self.app_name,
                document_type_id,
                document_type,
            )

        self.install_options = validate_install_options_config(
            install_option, "install"
        )
        self.uninstall_options = validate_install_options_config(
            uninstall_option,
            "uininstall",
            install=self.install_options,
        )

        # Version number is compliant with PEP440 (and related updates):
        try:
            # If input is already a version object (can happen by copying), use as-is
            if isinstance(version, Version):
                self.version = version
            else:
                self.version = Version(version)
        except (InvalidVersion, TypeError):
            raise InvalidVersionError(
                f"Version number for {self.app_name!r} ({self.version}) is not valid."
            ) from None

        if self.sources:
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

    def __eq__(self, other):
        if isinstance(other, AppConfig):
            return self.app_name == other.app_name
        return NotImplemented

    def __hash__(self):
        return hash(self.app_name)

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
        return self.app_name.replace("_", "-").lower()

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

    @property
    def dist_info_name(self):
        """The name of the .dist-info directory for the app."""
        return f"{self.module_name}.dist-info"

    def PYTHONPATH(self):
        """The PYTHONPATH modifications needed to run this app."""
        paths = []
        sources = self.sources.copy() if self.sources else []
        if self.test_mode and self.test_sources:
            sources.extend(self.test_sources)

        for source in sources:
            path = "/".join(source.rsplit("/", 1)[:-1])
            if path not in paths:
                paths.append(path)
        return paths

    def all_sources(self) -> list[str]:
        """Get all sources of the application that should be copied to the app.

        :returns: The Path to the dist-info folder.
        """
        sources = self.sources.copy() if self.sources else []
        if self.test_mode and self.test_sources:
            sources.extend(self.test_sources)
        return sources

    def main_module(self):
        """The path to the main module for the app.

        In normal operation, this is ``app.module_name``; however,
        in test mode, it is prefixed with ``tests.``.
        """
        if self.test_mode:
            return f"tests.{self.module_name}"
        else:
            return self.module_name


class FinalizedAppConfig(AppConfig):
    """An AppConfig that has been through platform finalization.

    Constructed by ``finalize_app_config()``; holds runtime attributes
    (``test_mode``, ``debugger``, etc.) that are not part of the parsed
    project configuration.
    """

    def __init__(
        self,
        app: AppConfig,
        *,
        test_mode: bool = False,
        debugger: BaseDebugger | None = None,
        debugger_host: str | None = None,
        debugger_port: int | None = None,
    ):
        self.__dict__.update(app.__dict__)
        self.test_mode = test_mode
        self.debugger = debugger
        self.debugger_host = debugger_host
        self.debugger_port = debugger_port


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


def get_license_from_text(license_text: str, default: str | None = None) -> str | None:
    """Infer the SPDX license identifier from the text of a license file.

    The order of pattern matching is important: more specific patterns must precede
    overlapping broader ones (e.g. GPL-3.0+ before GPL-3.0).  MIT is checked last
    because common words like "PERMITTED" produce false positives.

    :param license_text: Full text of the license file.
    :param default: The value to return if the license cannot be determined. Defaults
        to `None`.
    :returns: One of the recognised SPDX expressions, or `default` when the text
        cannot be matched to a known license.
    """
    hint_patterns = {
        "Apache-2.0": ["Apache"],
        "BSD-3-Clause": [
            "Redistribution and use in source and binary forms",
            "BSD",
        ],
        "GPL-2.0+": [
            "Free Software Foundation, either version 2 of the License",
            "GPLv2+",
        ],
        "GPL-2.0": [
            "version 2 of the GNU General Public License",
            "GPLv2",
        ],
        "GPL-3.0+": [
            "either version 3 of the License",
            "GPLv3+",
        ],
        "GPL-3.0": [
            "version 3 of the GNU General Public License",
            "GPLv3",
        ],
        "MIT": [
            "Permission is hereby granted, free of charge",
            "MIT",
        ],
    }
    for license_id, license_patterns in hint_patterns.items():
        for license_pattern in license_patterns:
            if license_pattern.lower() in license_text.lower():
                return license_id

    return default


def _write_temp_license(base_path: Path, app_name: str, text: str) -> str | None:
    """Write a temporary license file based on license text if needed.

    If the license text is more than one line, write a temporary file into the build
    folder, and return that path. If the license text is a single line, no file
    will be written, and `None` will be returned.

    :param base_path: The project base directory (parent of `pyproject.toml`), used to
        read license files and write temporary license text files.
    :param app_name: The app name
    :param text: The license text to use in the file.
    :returns: The path to the temporary file, as a string that can be used as part of a
        `license_files` declaration; or `None` if no temporary license file is needed.
    """
    if "\n" in text:
        tmp_license_file = f"build/license_text.{app_name}.txt"
        license_text_file = Path(base_path) / tmp_license_file
        license_text_file.parent.mkdir(parents=True, exist_ok=True)
        license_text_file.write_text(text, encoding="utf-8")
        return tmp_license_file
    else:
        return None


def _normalize_pep639_license_config(
    config: AppConfig,
    app_name: str,
    base_path: Path,
    console,
):
    """Finish normalizing a PEP 639 license config.

    :param config: The fully-merged config dict (mutated in place).
    :param app_name: The app name.
    :param base_path: The project base directory (parent of `pyproject.toml`), used
        to read license files and write temporary license text files.
    :param console: The Briefcase `Console` object used for warning output.
    """
    raw_license = config["license"]
    # Remove the `license-files` key because it needs to be converted into attribute
    # form (`license_files`)
    raw_license_files = config.pop("license-files", None)

    # Ensure we license-files is a list.
    if raw_license_files is None:
        raw_license_files = []

    # Ensure `licence` is an SPDX expression
    try:
        spdx_id = canonicalize_license_expression(raw_license)
    except InvalidLicenseExpression:
        raise BriefcaseConfigError(f"""\
The license configuration for '{app_name}' is in PEP 639 format, but the
`license` value {raw_license!r} is not a valid SPDX expression.

Update the `license` definition to a valid SPDX expression.
        """) from None

    # Validate each license-file exists.
    for license_path_str in raw_license_files:
        if not (Path(base_path) / license_path_str).is_file():
            raise BriefcaseConfigError(
                f"The license file {license_path_str!r} for '{app_name}' "
                f"does not exist."
            ) from None

    # Finalize PEP 639 config. Use `license_files` rather than `license-files` so it's a
    # valid attribute name.
    config["license"] = spdx_id
    config["license_files"] = raw_license_files


def _normalize_pep621_license_text_config(
    config: AppConfig,
    app_name: str,
    base_path: Path,
    console,
):
    """Normalize a PEP 621 license.text config into PEP 639 form.

    Text could be a license identifier (which *might* even be valid SPDX), or full
    license text. If the text is more than one line, write the value as a temporary
    license file.

    :param config: The fully-merged config dict (mutated in place).
    :param app_name: The app name.
    :param base_path: The project base directory (parent of `pyproject.toml`), used to
        read license files and write temporary license text files.
    :param console: The Briefcase `Console` object used for warning output.
    """
    license_text = config["license"]["text"]

    # Attempt to identify the SPDX expression from the text content.
    spdx_id = get_license_from_text(license_text)

    warning = [
        f"""
*******************************************************************************
** {"WARNING: '" + app_name + "' uses PEP 621 `license.text` format":73} **
*******************************************************************************

    Briefcase now uses PEP 639 format for license definitions.
"""
    ]
    if spdx_id is not None:
        # SPDX identifiable.
        license = spdx_id
        warning.append(f"""
    PEP 639 requires the definition of both `license` and `license-files`,
    and `license` must be a valid SPDX expression. The current value for
    `license.text` seems to define a SPDX license of '{spdx_id}'.
""")
    else:
        # SPDX not identifiable.
        spdx_id = "<SPDX expression>"
        license = "LicenseRef-UnknownLicense"
        warning.append(f"""
    PEP 639 requires the definition of both `license` and `license-files`.
    Briefcase cannot determine the current license for '{app_name}' based
    on the value of `license.text`. A value of 'LicenseRef-UnknownLicense'
    will be used.
""")

    # Write the license text to a file under the build directory so it can
    # be referenced as a real path in license-files.
    tmp_license_file = _write_temp_license(base_path, app_name, license_text)
    if tmp_license_file:
        license_files = [tmp_license_file]
        warning.append("""
    The contents of `license.text` will be used as the contents of the
    license file. This may not be correct, and should be verified.
""")
    else:
        license_files = []
        warning.append("""
    Your project will not have a value for `license-files`. This will
    cause problems packaging for some platforms.
""")

    warning.append(f"""
    Update your configuration to put the full license text in a file and use
    PEP 639 format for the license definition:

        license = "{spdx_id}"
        license-files = ["LICENSE"]

    You should not release your project without resolving this warning.

*******************************************************************************
""")

    # Warn and finalize PEP 621 license.text coercion. Use `license_files` rather than
    # `license-files` so it's a valid attribute name.
    console.warning("".join(warning))
    config["license"] = license
    config["license_files"] = license_files


def _normalize_pep621_license_file_config(
    config: AppConfig,
    app_name: str,
    base_path: Path,
    console,
):
    """Normalize a PEP 621 license.file config into PEP 639 form.

    Read the file to infer the SPDX expression.

    :param config: The fully-merged config dict (mutated in place).
    :param app_name: The app name.
    :param base_path: The project base directory (parent of `pyproject.toml`), used
        to read license files and write temporary license text files.
    :param console: The Briefcase `Console` object used for warning output.
    """
    license_file = config["license"]["file"]
    license_path = Path(base_path) / license_file
    if not license_path.is_file():
        raise BriefcaseConfigError(
            f"The PEP 621 license.file {license_file!r} for '{app_name}' "
            "does not exist."
        ) from None
    license_text = license_path.read_text(encoding="utf-8")
    spdx_id = get_license_from_text(license_text)

    warning = [
        f"""
*******************************************************************************
** {"WARNING: '" + app_name + "' uses PEP 621 `license.file` format":73} **
*******************************************************************************

    Briefcase now uses PEP 639 format for license definitions.

    PEP 639 requires the definition of both `license` and `license-files`.
    The value for `license.file` will be used to populate the PEP 639
    `licence-files` setting.
"""
    ]
    if spdx_id is not None:
        license = spdx_id
        # License is valid SPDX
        warning.append(f"""
    The license has been identified as '{spdx_id}'.
""")
    else:
        # Can't identify SPDX for license
        license = "<SPDX expression>"
        spdx_id = "LicenseRef-UnknownLicense"
        warning.append("""
    A license SPDX expression could not be identified from the license file.
    The license has been set to 'LicenseRef-UnknownLicense'
    """)

    warning.append(f"""
    Update your configuration to use PEP 639 format:

        license = "{license}"
        license-files = ["{license_file}"]

    You should not release your project without resolving this warning.

*******************************************************************************
""")
    # Warn and finalize PEP 621 license.file coercion. Use `license_files` rather than
    # `license-files` so it's a valid attribute name.
    console.warning("".join(warning))
    config["license"] = spdx_id
    config["license_files"] = [license_file]


def _normalize_pre_pep621_license_config(
    config: AppConfig,
    app_name: str,
    base_path: Path,
    console,
):
    """Normalize a pre-PEP 621 license config into PEP 639 form.

    Pre-PEP 621 free-form `license` text, with no license-files. We also know that the
    license text isn't a valid SPDX expression, because preprocessing caught that case.

    Treat like the PEP 621 license.text case: write the string value to a file, set
    license-files to point at it, and attempt to canonicalize the SPDX expression.

    :param config: The fully-merged config dict (mutated in place).
    :param app_name: The app name.
    :param base_path: The project base directory (parent of `pyproject.toml`), used to
        read license files and write temporary license text files.
    :param console: The Briefcase `Console` object used for warning output.
    """
    license_text = config["license"]

    # Attempt to identify the SPDX expression from the text content.
    spdx_id = get_license_from_text(license_text)

    warning = [
        f"""
*******************************************************************************
** {"WARNING: '" + app_name + "' uses pre-PEP 621 `license` format":73} **
*******************************************************************************

    Briefcase now uses PEP 639 format for license definitions.
"""
    ]
    if spdx_id is not None:
        # SPDX identifiable.
        license = spdx_id
        warning.append(f"""
    PEP 639 requires the definition of both `license` and `license-files`,
    and `license` must be a valid SPDX expression. The current value for
    `license` seems to define a SPDX license of '{spdx_id}'.
""")
    else:
        # SPDX not identifiable.
        spdx_id = "<SPDX expression>"
        license = "LicenseRef-UnknownLicense"
        warning.append(f"""
    PEP 639 requires the definition of both `license` and `license-files`.
    Briefcase cannot determine the current license for '{app_name}' based
    on the value of `license`. A value of 'LicenseRef-UnknownLicense' will
    be used.
""")

    # Write the license text to a file under the build directory so it can
    # be referenced as a real path in license-files.
    tmp_license_file = _write_temp_license(base_path, app_name, license_text)
    if tmp_license_file:
        license_files = [tmp_license_file]
        warning.append("""
    The contents of `license` will be used as the contents of the license
    file. This may not be correct, and should be verified.
""")
    else:
        license_files = []
        warning.append("""
    Your project will not have a value for `license-files`. This will
    cause problems packaging for some platforms.
""")

    warning.append(f"""
    Update your configuration to put the full license text in a file and use
    PEP 639 format for the license definition:

        license = "{spdx_id}"
        license-files = ["LICENSE"]

    You should not release your project without resolving this warning.

*******************************************************************************
""")

    # Warn and finalize pre-PEP 621 license coercion. Use `license_files` rather than
    # `license-files` so it's a valid attribute name.
    console.warning("".join(warning))
    config["license"] = license
    config["license_files"] = license_files


def normalize_license_config(
    config: AppConfig,
    app_name: str,
    base_path: Path,
    console,
):
    """Normalize the `license` and `license-files` entries in a merged config.

    This runs after all config layers (project, global, app, platform, format) have been
    merged.  It coerces legacy formats to the PEP 639 two-field representation, emits
    deprecation warnings for out-of-date configurations, and raises
    `BriefcaseConfigError` for invalid or ambiguous configurations.

    :param config: The fully-merged config dict (mutated in place).
    :param app_name: The app name.
    :param base_path: The project base directory (parent of `pyproject.toml`), used to
        read license files and write temporary license text files.
    :param console: The Briefcase `Console` object used for warning output.
    """
    raw_license = config.get("license")
    raw_license_files = config.get("license-files")

    # PEP 621 table + license-files is always an error
    if isinstance(raw_license, dict) and raw_license_files is not None:
        raise BriefcaseConfigError(f"""
The license configuration for '{app_name}' mixes PEP 621 table format
(`license.file`) with PEP 639 format (`license-files`).

Update your configuration to use PEP 639 format:

    license = "<SPDX expression>"
    license-files = ["LICENSE"]
""") from None

    # license_files without a license expression is always an error
    if raw_license is None and raw_license_files is not None:
        raise BriefcaseConfigError(f"""\
The license configuration for '{app_name}' defines `license-files` but no
`license` SPDX expression.

Add a `license` field with the SPDX expression for your project:

    license = "<SPDX expression>"
    license-files = ["LICENSE"]
""") from None

    # If license is a string, attempt to validate license as an SPDX value.
    # If it is valid SPDX, and license-files is undefined, set the license
    # list to be empty. This allows us to differentiate pre-PEP 621 format
    # from PEP 639 format.
    if isinstance(raw_license, str):
        try:
            canonicalize_license_expression(raw_license)
            if raw_license_files is None:
                raw_license_files = []
        except InvalidLicenseExpression:
            pass

    # Now finalize the license configuration
    if isinstance(raw_license, str) and raw_license_files is not None:
        # `license` and `license-files` - Valid PEP 639
        _normalize_pep639_license_config(config, app_name, base_path, console)

    elif isinstance(raw_license, dict):
        # license is a TOML table
        if list(raw_license.keys()) == ["text"]:
            # `license.text` - PEP 621 text format
            _normalize_pep621_license_text_config(config, app_name, base_path, console)

        elif list(raw_license.keys()) == ["file"]:
            # `license.file` - PEP 621 file format
            _normalize_pep621_license_file_config(config, app_name, base_path, console)
        else:
            # PEP 621 `license` table contains anything else
            raise BriefcaseConfigError(f"""\
The project configuration for '{app_name}' defines an invalid PEP 621
`license` table.

Update your configuration to provide a valid PEP 639 configuration:

    license = "<SPDX expression>"
    license-files = ["LICENSE"]
""") from None

    elif isinstance(raw_license, str):
        # Pre-PEP 621 format: Just a `license` string, but *not* an SPDX value.
        _normalize_pre_pep621_license_config(config, app_name, base_path, console)
    else:
        # No license definition — license of *some* form is a required value.
        raise BriefcaseConfigError(
            f"Configuration for {app_name!r} does not contain "
            "a valid PEP 639 license definition."
        )


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
    maybe_update("license-files", "license-files")
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


def parse_config(config_file: Path, platform, output_format, console):
    """Parse the briefcase section of the pyproject.toml configuration file.

    This method only does basic structural parsing of the TOML, looking for,
    at a minimum, a `[tool.briefcase.app.<appname>]` section declaring the
    existence of a single app. It will also search for:

    - `[tool.briefcase]` - global briefcase settings
    - `[tool.briefcase.app.<appname>]` - settings specific to the app
    - `[tool.briefcase.app.<appname>.<platform>]` - settings specific to the platform
    - `[tool.briefcase.app.<appname>.<platform>.<format>]` - settings specific to the
      output format

    A configuration can define multiple apps; the final output is the merged
    content of the global, app, platform and output format settings
    for each app, with output format definitions taking precedence over
    platform, over app-level, over global. The final result is a single
    (mostly) flat dictionary for each app.

    :param config_file: A `Path` to the `pyproject.toml` file to be parsed.
        The parent directory of this file is used as the project base path for
        any on-disk operations (e.g., writing temporary license text files).
    :param platform: The platform being targeted
    :param output_format: The output format
    :param console: The console to use for any output or logging.
    :returns: A dictionary of configuration data. The top level dictionary is
        keyed by the names of the apps that are declared; each value is
        itself the configuration data merged from global, app, platform and
        format definitions.
    """
    base_path = config_file.parent
    try:
        with config_file.open("rb") as f:
            pyproject = tomllib.load(f)
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

        # Normalize license fields to PEP 639 representation.
        normalize_license_config(config, app_name, base_path, console)

        # Construct a configuration object, and add it to the list
        # of configurations that are being handled.
        app_configs[app_name] = config

    return global_config, app_configs
