# import argparse
from pathlib import Path

import tomli_w
from platformdirs import PlatformDirs

from .base import BaseCommand


class ConfigCommand(BaseCommand):
    command = "config"
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
            config = self.tools.toml.load(config_path.open("rb"))

        # Split key into nested structure
        keys = key.split(".")
        current = config
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value

        with config_path.open("wb") as f:
            tomli_w.dump(config, f)

    def __call__(self, key, value, global_config=False, **options):
        if global_config:
            config_path = (
                Path(PlatformDirs("org.beeware.briefcase", "Beeware").user_config_dir)
                / "config.toml"
            )
        else:
            config_path = self.base_path / ".briefcase" / "config.toml"

        self.write_config(config_path, key, value)
        self.logger.info(
            f"Set {'global' if global_config else 'project'} config: {key} = {value}"
        )
