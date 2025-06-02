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
    description = "Set and store per-user configuration values for Briefcase."
    help = "Configure per-project or global settings."

    def add_options(self, parser):
        parser.add_argument(
            "key",
            help="The configuration key (e.g., iOS.device)",
        )
        parser.add_argument(
            "value",
            help="The value to set",
        )
        parser.add_argument(
            "--global",
            dest="global_config",
            action="store_true",
            help="Set the configuration value globally instead of for this this project.",
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
        if "." not in key:
            raise BriefcaseConfigError("Key must be in the format 'section.option")

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

        self.write_config(config_path, key, value)
        self.console.info(
            f"Set {'global' if global_config else 'project'} config: {key} = {value}"
        )

    def binary_path(self, app):
        raise NotImplementedError("ConfigCommand does not use binary_path.")

    def output_format(self):
        raise NotImplementedError("ConfigCommand does not use output_format.")

    def distribution_path(self, app):
        raise NotImplementedError("ConfigCommand does not use distribution_path.")

    def bundle_path(self, app):
        raise NotImplementedError("ConfigCommand does not use bundle_path.")

    def binary_executable_path(self, app):
        raise NotImplementedError("ConfigCommand does not use binary_executable_path.")
