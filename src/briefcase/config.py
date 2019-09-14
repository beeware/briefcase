import toml

from briefcase.platforms import get_output_formats, get_platforms

from .exceptions import BriefcaseConfigError


class GlobalConfig:
    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __repr__(self):
        return "<GlobalConfig>"


class AppConfig:
    def __init__(
        self,
        name,
        version,
        bundle,
        icon=None,
        splash=None,
        **kwargs
    ):
        self.name = name
        self.version = version
        self.bundle = bundle

        # icon can be specified as a single filename,
        # or as a dictionary of files, keyed by size in pixels
        if icon is not None:
            try:
                self.icon = {
                    str(size): filename
                    for size, filename in icon.items()
                }
            except AttributeError:
                self.icon = icon

        # splash can be specified as a single filename,
        # or as a dictionary of files, keyed by dimensions in pixels
        # (width x height)
        if splash is not None:
            try:
                self.splash = {
                    str(size): filename
                    for size, filename in splash.items()
                }
            except AttributeError:
                self.splash = splash

        # Extra arguments
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __repr__(self):
        return "<AppConfig {bundle}.{name} v{version}>".format(
            bundle=self.bundle,
            name=self.name,
            version=self.version,
        )

    @property
    def has_scaled_icon(self):
        """
        Does the config's icon provide multiple sizes?

        Raises an AttributeError if no icon has been defined.
        """
        return isinstance(self.icon, dict)

    @property
    def has_scaled_splash(self):
        """
        Does the config's splash provide multiple sizes?

        Raises an AttributeError if no splash has been defined.
        """
        return isinstance(self.splash, dict)


def parse_config(config_file, platform, output_format):
    """
    Parse the briefcase section of the pyproject.toml configuration file.

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
    for each app, with output format definitions taking precendence over
    platform, over app-level, over global. The final result is a single
    (mostly) flat dictionary for each app.

    :param config_file: A file-like object containing TOML to be parsed.
    :param platform: The platform being targetted
    :param output_format: The output format
    :returns: A dictionary of configuration data. The top level dictionary is
        keyed by the names of the apps that are declared; each value is
        itself the configuration data merged from global, app, platform and
        format definitions.
    """
    try:
        pyproject = toml.load(config_file)

        global_config = pyproject['tool']['briefcase']
    except toml.TomlDecodeError as e:
        raise BriefcaseConfigError('Invalid pyproject.toml: {e}'.format(e=e))
    except KeyError:
        raise BriefcaseConfigError('No tool.briefcase section in pyproject.toml')

    # For consistent results, sort the platforms and formats
    all_platforms = sorted(get_platforms().keys())
    all_formats = sorted(get_output_formats(platform).keys())

    try:
        all_apps = global_config.pop('app')
    except KeyError:
        raise BriefcaseConfigError('No Briefcase apps defined in pyproject.toml')

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
                        platform_data.update(format_data)

            except KeyError:
                pass

        # Now construct the final configuration.
        # The app's config starts as a copy of the base briefcase configuation.
        config = global_config.copy()

        # The app name is both the key, and a property of the configuration
        config['name'] = app_name

        # Then overwrite the explicit app-specific configuration data
        config.update(app_data)

        # If there is platform-specific configuration, overwrite those values.
        # This will already include any format-specific configuration.
        if platform_data:
            config.update(platform_data)

        # Construct a configuration object, and add it to the list
        # of configurations that are being handled.
        app_configs[app_name] = config

    return global_config, app_configs
