from pathlib import Path

import tomli
from platformdirs import PlatformDirs


class Config:
    def __init__(self, tools):
        self.tools = tools
        self._project_config = None
        self._global_config = None

    def load_toml(self, path):
        if path.exists():
            with path.open("rb") as f:
                return tomli.load(f)
        return {}

    def get(self, key: str, cli_value=None, prompt=None, choices=None):
        if cli_value == "?":
            return self.tools.input.selection(prompt, choices)

        if cli_value is not None:
            return cli_value

        # Project config
        if self._project_config is None:
            self._project_config = self.load_toml(
                self.tools.base_path / ".briefcase" / "config.toml"
            )
        value = self._get_nested(self._project_config, key)
        if value is not None:
            return value

        # Global config
        if self._global_config is None:
            config_path = (
                Path(PlatformDirs("org.beeware.briefcase", "Beeware").user_config_dir)
                / "config.toml"
            )
            self._global_config = self.load_toml(config_path)
        value = self._get_nested(self._global_config, key)
        if value is not None:
            return value

        # pyproject.toml
        value = self._get_nested(self.tools.config.project, key)
        return value

    def _get_nested(self, config, dotted_key):
        parts = dotted_key.split(".")
        for part in parts:
            if not isinstance(config, dict) or part not in config:
                return None
            config = config[part]
        return config
