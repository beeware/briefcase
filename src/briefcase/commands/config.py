from pathlib import Path

import tomli
import tomli_w
from platformdirs import PlatformDirs

from briefcase.exceptions import BriefcaseConfigError

from .base import BaseCommand


class ConfigCommand(BaseCommand):
    """Command to modify Briefcase configuration settings.

    Allows setting of individual configuration keys within either a
    project-level or global configuration file. Useful for scripting
    or user-driven configuration outside of interactive prompts.
    """

    command = "config"
    platform = None
    output_format = None
    description = (
        "Set a configuration value for the current project or globally using the --global flag.\n\n"
        "Configuration is stored in .briefcase/config.toml or the global config path.\n"
        "Use keys like:\n"
        "  - author.name\n"
        "  - author.email\n"
        "  - iOS.device\n"
        "  - android.device\n"
        "  - macOS.identity\n"
        "  - network.proxy\n"
        "  - network.cache_path\n\n"
        "Precedence: CLI > project config > global config."
    )
    help = "Configure per-project or global settings."

    def add_options(self, parser):
        parser.add_argument(
            "key",
            help="The configuration key (e.g., author.name, iOS.device)",
        )
        parser.add_argument(
            "value",
            help="The value to assign to the key",
        )
        parser.add_argument(
            "--global",
            dest="global_config",
            action="store_true",
            help="Set the configuration value globally instead of for this project.",
        )

    def write_config(self, config_path, key, value):
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = {}
        if config_path.exists():
            try:
                with config_path.open("rb") as f:
                    config = tomli.load(f)
            except PermissionError as e:
                raise BriefcaseConfigError(f"Unable to read config file: {e}")

        # Split key into nested structure
        keys = key.split(".")
        current = config
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value

        try:
            with config_path.open("wb") as f:
                tomli_w.dump(config, f)
        except PermissionError as e:
            raise BriefcaseConfigError(f"Unable to write config file: {e}")

    def __call__(self, key: str, value: str, global_config: bool = False, **options):
        """Set a configuration value in a Briefcase project or global config.

        Stores the provided key-value pair in either the project's config.toml
        or the user's global config.toml file, depending on the --global flag.

        :param key: The configuration key to set, as a dot-delimited path.
        :param value: The value to assign to the configuration key.
        :param global_config: Should the global config file be modified instead of the
        project-level one?
        :param options: Additional keyword options passed to the command (unused).
        """
        parts = key.split(".")
        if len(parts) < 2 or any(not part.strip() for part in parts):
            raise BriefcaseConfigError(f"Invalid configuration key: '{key}'")

        if global_config:
            config_path = (
                Path(PlatformDirs("org.beeware.briefcase", "Beeware").user_config_dir)
                / "config.toml"
            )
        else:
            pyproject = Path.cwd() / "pyproject.toml"
            # Ensure base_path is valid
            if (
                not pyproject.exists()
                or "[tool.briefcase]" not in pyproject.read_text()
            ):
                raise BriefcaseConfigError(
                    "Not a valid Briefcase project: pyproject.toml missing or invalid."
                )

            self.tools.base_path = Path.cwd()
            config_path = self.tools.base_path / ".briefcase" / "config.toml"

        try:
            self.write_config(config_path, key, value)
        except PermissionError:
            raise BriefcaseConfigError(
                "Unable to write configuration file due to permission error."
            )

        self.console.info(
            f"Set {'global' if global_config else 'project'} config: {key} = {value}"
        )

    def binary_path(self, app):
        raise NotImplementedError("ConfigCommand does not use binary_path.")

    def distribution_path(self, app):
        raise NotImplementedError("ConfigCommand does not use distribution_path.")

    def bundle_path(self, app):
        raise NotImplementedError("ConfigCommand does not use bundle_path.")

    def binary_executable_path(self, app):
        raise NotImplementedError("ConfigCommand does not use binary_executable_path.")
