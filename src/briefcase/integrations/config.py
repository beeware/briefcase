from pathlib import Path

import tomli
from platformdirs import PlatformDirs

from briefcase.exceptions import BriefcaseCommandError

__all__ = ["Config"]


class Config:
    """Resolve configuration values from CLI, project config,
    global config and pyproject.toml, in that order
    """

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
        """Retrieve a config value with full precedence resolution and
        optional prompt support.
        """
        # Explicit prompt request via command line
        if cli_value == "?":
            return self.tools.input.selection(prompt, choices)

        # Direct CLI value
        if cli_value is not None:
            return cli_value

        # Project-level user config (.briefcase/config.toml)
        if self._project_config is None:
            self._project_config = self.load_toml(
                self.tools.base_path / ".briefcase" / "config.toml"
            )
        value = self._get_nested(self._project_config, key)
        if value is not None:
            return value

        # Global user config (~/.config/BeeWare/Briefcase/config.toml)
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
        app_configs = getattr(self.tools, "app_configs", None)
        if app_configs:
            parts = key.split(".")
            if parts[0] in app_configs:
                app_config = app_configs[parts[0]]
                try:
                    for part in parts[1:]:
                        app_config = getattr(app_config, part)
                    return app_config
                except AttributeError:
                    pass
            elif len(app_configs) == 1:
                app_config = list(app_configs.values())[0]
                try:
                    for part in parts:
                        app_config = getattr(app_config, part)
                    return app_config
                except AttributeError:
                    pass
            else:
                raise BriefcaseCommandError(
                    "Project specifies more than one application; specify the app name in the key (e.g., 'myapp.setting')."
                )

    def _get_nested(self, config, dotted_key):
        """Traverse a nested dictionary using a dotted key like 'iOS.device'"""
        parts = dotted_key.split(".")
        for part in parts:
            if not isinstance(config, dict) or part not in config:
                return None
            config = config[part]
        return config
