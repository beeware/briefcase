import pytest

from ....utils import create_file, create_wheel


@pytest.fixture
def first_app_generated(first_app_config, tmp_path):
    # Create the briefcase.toml file
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"
    create_file(
        bundle_path / "briefcase.toml",
        """
[paths]
app_path="app"
app_requirements_path="requirements.txt"
""",
    )

    # Create index.html
    create_file(bundle_path / "www" / "index.html", "<html></html>")

    # Create the initial briefcase.css
    create_file(
        bundle_path / "www" / "static" / "css" / "briefcase.css",
        """
#pyconsole {
  display: None;
}
/*******************************************************************
 ******************** Wheel contributed styles ********************/
""",
    )

    # Create an empty wheels folder
    (bundle_path / "www" / "static" / "wheels").mkdir(parents=True)

    return first_app_config


@pytest.fixture
def first_app_built(first_app_generated, tmp_path):
    bundle_path = tmp_path / "base_path" / "web" / "static" / "First App"

    # Create pyscript.toml
    create_file(
        bundle_path / "www" / "pyscript.toml",
        'packages = ["dummy-1.2.3-py3-none-all.whl"]',
    )

    # Create an app wheel
    create_wheel(bundle_path / "www" / "static" / "wheels")

    return first_app_generated
