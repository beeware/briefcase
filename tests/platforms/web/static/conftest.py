import pytest

from ....utils import create_file, create_wheel


@pytest.fixture
def first_app_generated(first_app_config, tmp_path):
    # Create the briefcase.toml file
    bundle_path = tmp_path / "base_path/build/first-app/web/static"
    create_file(
        bundle_path / "briefcase.toml",
        """
[paths]
app_path="app"
app_requirements_path="requirements.txt"
""",
    )

    # Create index.html with insert markers
    create_file(
        bundle_path / "www/index.html",
        """<!doctype html>
<html>
  <head>
    <!--@@ head:start @@-->
    <!--@@ head:end @@-->
    <!--@@ Python:start @@-->
    <!--@@ Python:end @@-->
  </head>
  <body>
    <div id="briefcase-splash"></div>

    <!--@@ body-end:start @@-->
    <!--@@ body-end:end @@-->
  </body>
</html>
""",
    )

    # Create the initial briefcase.css with CSS insert markers
    create_file(
        bundle_path / "www/static/css/briefcase.css",
        """
/*@@ CSS:start @@*/
/*@@ CSS:end @@*/

#pyconsole {
  display: None;
}
/*******************************************************************
 ******************** Wheel contributed styles ********************/
""",
    )

    # Create an empty wheels folder
    (bundle_path / "www/static/wheels").mkdir(parents=True)

    return first_app_config


@pytest.fixture
def first_app_built(first_app_generated, tmp_path):
    bundle_path = tmp_path / "base_path/build/first-app/web/static"

    # Create an app wheel
    create_wheel(bundle_path / "www/static/wheels")

    return first_app_generated
