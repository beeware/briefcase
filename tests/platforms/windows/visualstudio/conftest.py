from textwrap import dedent

import pytest

from ....utils import create_file


@pytest.fixture
def first_app_templated(first_app_config, tmp_path):
    bundle_path = tmp_path / "base_path/build/first-app/windows/visualstudio"

    create_file(
        bundle_path / "briefcase.toml",
        dedent(
            """\
            [paths]
            app_path = "src/app"
            app_packages_path = "src/app_packages"
            extras_path = "custom_extras"
            """
        ),
    )

    return first_app_config
