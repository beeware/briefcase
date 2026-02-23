import sys

import pytest
from packaging.version import Version

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseConfigError

from .test_GlobalConfig import VALID_VERSIONS


def test_minimal_AppConfig():
    """A simple config can be defined."""
    config = AppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=["src/myapp", "somewhere/else/interesting", "local_app"],
        license={"file": "LICENSE"},
    )

    # The basic properties have been set.
    assert config.app_name == "myapp"
    assert config.version == Version("1.2.3")
    assert config.bundle == "org.beeware"
    assert config.description == "A simple app"
    assert config.requires is None
    assert config.sources == ["src/myapp", "somewhere/else/interesting", "local_app"]
    assert config.external_package_path is None
    assert config.external_package_executable_path is None

    # Derived properties have been set.
    assert config.bundle_name == "myapp"
    assert config.bundle_identifier == "org.beeware.myapp"
    assert config.formal_name == "myapp"
    assert config.class_name == "myapp"
    assert config.document_types == {}

    # There is no icon of any kind
    assert config.icon is None

    # The PYTHONPATH is derived correctly
    config.test_mode = False
    assert config.PYTHONPATH() == ["src", "somewhere/else", ""]
    # The test mode PYTHONPATH is the same
    config.test_mode = True
    assert config.PYTHONPATH() == ["src", "somewhere/else", ""]

    # The object has a meaningful REPL
    assert repr(config) == "<org.beeware.myapp v1.2.3 AppConfig>"


def test_minimal_external_AppConfig():
    """A simple config for an external app can be defined."""
    config = AppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        license={"file": "LICENSE"},
        external_package_path="path/to/package",
        external_package_executable_path="internal/app.exe",
    )

    # The basic properties have been set.
    assert config.app_name == "myapp"
    assert config.version == Version("1.2.3")
    assert config.bundle == "org.beeware"
    assert config.description == "A simple app"
    assert config.requires is None
    assert config.sources is None
    assert config.external_package_path == "path/to/package"
    assert config.external_package_executable_path == "internal/app.exe"

    # Derived properties have been set.
    assert config.bundle_name == "myapp"
    assert config.bundle_identifier == "org.beeware.myapp"
    assert config.formal_name == "myapp"
    assert config.class_name == "myapp"
    assert config.document_types == {}

    # There is no icon of any kind
    assert config.icon is None

    # The PYTHONPATH is derived correctly
    config.test_mode = False
    assert config.PYTHONPATH() == []
    # The test mode PYTHONPATH is the same
    config.test_mode = True
    assert config.PYTHONPATH() == []

    # The object has a meaningful REPL
    assert repr(config) == "<org.beeware.myapp v1.2.3 AppConfig>"


def test_extra_attrs():
    """A config can contain attributes in addition to those required."""
    config = AppConfig(
        app_name="myapp",
        formal_name="My App!",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        long_description="A longer description\nof the app",
        license={"file": "LICENSE"},
        template="/path/to/template",
        sources=["src/myapp"],
        requires=["first", "second", "third"],
        document_type={
            "document": {
                "icon": "icon",
                "extension": "doc",
                "description": "A document",
                "url": "https://testurl.com",
                "mime_type": "application/x-my-doc-type",
            }
        },
        first="value 1",
        second=42,
    )

    # The basic properties have been set.
    assert config.app_name == "myapp"
    assert config.version == Version("1.2.3")
    assert config.bundle == "org.beeware"
    assert config.description == "A simple app"
    assert config.long_description == "A longer description\nof the app"
    assert config.template == "/path/to/template"
    assert config.requires == ["first", "second", "third"]

    # Properties that are derived by default have been set explicitly
    assert config.formal_name == "My App!"
    assert config.class_name == "MyApp"

    if sys.platform == "darwin":
        assert config.document_types == {
            "document": {
                "icon": "icon",
                "extension": "doc",
                "description": "A document",
                "url": "https://testurl.com",
                "mime_type": "application/x-my-doc-type",
                "macOS": {
                    "CFBundleTypeRole": "Viewer",
                    "LSHandlerRank": "Owner",
                    "UTTypeConformsTo": [
                        "public.data",
                        "public.content",
                    ],
                    "is_core_type": False,
                },
            }
        }
    else:
        assert config.document_types == {
            "document": {
                "icon": "icon",
                "extension": "doc",
                "description": "A document",
                "url": "https://testurl.com",
                "mime_type": "application/x-my-doc-type",
            }
        }

    # Explicit additional properties have been set
    assert config.first == "value 1"
    assert config.second == 42

    # An attribute that wasn't provided raises an error
    with pytest.raises(AttributeError):
        _ = config.unknown


@pytest.mark.parametrize(
    "name",
    [
        "myapp",  # lowercase
        "myApp",  # contains uppercase
        "MyApp",  # initial uppercase
        "MyAPP",  # ends in uppercase
        "my-app",  # contains hyphen
        "my_app",  # contains underscore
        "myapp2",  # ends with digit
        "my2app",  # contains digit
    ],
)
def test_valid_app_name(name):
    try:
        AppConfig(
            app_name=name,
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=["src/" + name.replace("-", "_")],
            license={"file": "LICENSE"},
        )
    except BriefcaseConfigError:
        pytest.fail(f"{name} should be valid")


@pytest.mark.parametrize(
    "name",
    [
        "!myapp",  # initial punctuation
        "my!app",  # contains punctuation
        "myapp!",  # end punctuation
        "my$app",  # other punctuation
        "-myApp",  # initial hyphen
        "myApp-",  # end hyphen
        "_myApp",  # initial underscore
        "myApp_",  # end underscore
    ],
)
def test_invalid_app_name(name):
    with pytest.raises(BriefcaseConfigError, match=r"is not a valid app name\."):
        AppConfig(
            app_name=name,
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=["src/invalid"],
            license={"file": "LICENSE"},
        )


@pytest.mark.parametrize(
    "bundle",
    [
        "com.example",
        "com.example.more",
        "com.example42.more",
        "com.example-42.more",
    ],
)
def test_valid_bundle(bundle):
    try:
        AppConfig(
            app_name="myapp",
            version="1.2.3",
            bundle=bundle,
            description="A simple app",
            sources=["src/myapp"],
            license={"file": "LICENSE"},
        )
    except BriefcaseConfigError:
        pytest.fail(f"{bundle} should be valid")


@pytest.mark.parametrize(
    "bundle",
    [
        "not a bundle!",  # Free text.
        "home",  # Only one section.
        "com.hello_world",  # underscore
        "com.hello,world",  # comma
        "com.hello world!",  # exclamation point
    ],
)
def test_invalid_bundle_identifier(bundle):
    with pytest.raises(
        BriefcaseConfigError, match=r"is not a valid bundle identifier\."
    ):
        AppConfig(
            app_name="myapp",
            version="1.2.3",
            bundle=bundle,
            description="A simple app",
            sources=["src/invalid"],
            license={"file": "LICENSE"},
        )


@pytest.mark.parametrize(("input", "expected"), VALID_VERSIONS)
def test_valid_app_version(input, expected):
    config = AppConfig(
        app_name="myapp",
        version=input,
        bundle="org.beeware",
        description="A simple app",
        sources=["src/myapp"],
        license={"file": "LICENSE"},
    )

    # Version is parsed as an equivalent Version object
    assert config.version == Version(expected)
    # Serialized output of parsed Version matches the expected value
    assert str(config.version) == expected


def test_invalid_app_version():
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Version number for 'myapp' \(foobar\) is not valid\.",
    ):
        AppConfig(
            app_name="myapp",
            version="foobar",
            bundle="org.beeware",
            description="A simple app",
            sources=["src/invalid"],
            license={"file": "LICENSE"},
        )


@pytest.mark.parametrize(
    ("name", "module_name"),
    [
        ("myapp", "myapp"),
        ("my-app", "my_app"),
    ],
)
def test_module_name(name, module_name):
    config = AppConfig(
        app_name=name,
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=["src/" + module_name],
        license={"file": "LICENSE"},
    )

    assert config.module_name == module_name


@pytest.mark.parametrize(
    ("bundle", "package_name"),
    [
        ("com.example", "com.example"),
        ("com.ex-ample", "com.ex_ample"),
    ],
)
def test_package_name(bundle, package_name):
    config = AppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle=bundle,
        description="A simple app",
        sources=["src/myapp"],
        license={"file": "LICENSE"},
    )

    assert config.package_name == package_name


@pytest.mark.parametrize(
    ("app_name", "dist_info_name"),
    [
        ("my-app", "my_app.dist-info"),
        ("my_app", "my_app.dist-info"),
    ],
)
def test_dist_info_name(app_name, dist_info_name):
    config = AppConfig(
        app_name=app_name,
        version="1.2.3",
        bundle="com.example",
        description="A simple app",
        sources=["src/my_app"],
        license={"file": "LICENSE"},
    )

    assert config.dist_info_name == dist_info_name


@pytest.mark.parametrize(
    ("app_name", "bundle_name"),
    [
        ("my-app", "my-app"),
        ("my_app", "my-app"),
    ],
)
def test_bundle_name(app_name, bundle_name):
    config = AppConfig(
        app_name=app_name,
        version="1.2.3",
        bundle="com.example",
        description="A simple app",
        sources=["src/my_app"],
        license={"file": "LICENSE"},
    )

    assert config.bundle_name == bundle_name


@pytest.mark.parametrize(
    ("app_name", "bundle_name"),
    [
        ("my-app", "my-app"),
        ("my_app", "my-app"),
    ],
)
def test_bundle_identifier(app_name, bundle_name):
    bundle = "com.example"

    config = AppConfig(
        app_name=app_name,
        version="1.2.3",
        bundle=bundle,
        description="A simple app",
        sources=["src/my_app"],
        license={"file": "LICENSE"},
    )

    assert config.bundle_identifier == f"{bundle}.{bundle_name}"


@pytest.mark.parametrize(
    "sources",
    [
        ["src/dupe", "src/dupe"],
        ["src/dupe", "src/other", "src/dupe"],
        ["src/dupe", "somewhere/dupe", "src/other"],
        ["src/dupe", "src/deep/dupe", "src/other"],
    ],
)
def test_duplicated_source(sources):
    with pytest.raises(
        BriefcaseConfigError, match=r"contains duplicated package names\."
    ):
        AppConfig(
            app_name="dupe",
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=sources,
            license={"file": "LICENSE"},
        )


def test_no_source_for_app():
    with pytest.raises(
        BriefcaseConfigError, match=r" does not include a package named 'my_app'\."
    ):
        AppConfig(
            app_name="my-app",
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=["src/something", "src/other"],
            license={"file": "LICENSE"},
        )


@pytest.mark.parametrize(
    ("install_launcher", "console_app", "expected"),
    [
        (True, False, True),
        (False, False, False),
        (None, False, True),
        #
        (True, True, True),
        (False, True, False),
        (None, True, False),
    ],
)
def test_install_launcher(install_launcher, console_app, expected):
    config = AppConfig(
        app_name="my-app",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        license={"file": "LICENSE"},
        install_launcher=install_launcher,
        console_app=console_app,
    )
    assert config.install_launcher == expected


def test_non_unique_uninstall_options():
    """Installer and Uninstaller options must not overlap."""
    with pytest.raises(
        BriefcaseConfigError,
        match=(
            r"Uininstall option names must be unique. "
            r"The name 'first' is already used as an install option."
        ),
    ):
        AppConfig(
            app_name="myapp",
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=["src/myapp"],
            license={"file": "LICENSE"},
            install_option=[
                {
                    "name": "first",
                    "title": "First option",
                    "description": "Do the first thing",
                    "default": True,
                },
                {
                    "name": "second",
                    "title": "Second option",
                    "description": "Do the second thing",
                    "default": False,
                },
            ],
            uninstall_option=[
                {
                    "name": "first",
                    "title": "First option",
                    "description": "Do the first thing",
                    "default": True,
                },
            ],
        )


def test_capitalization():
    """Capitalization is prohibited and normalized out in some properties."""
    config = AppConfig(
        app_name="MyApp",
        version="1.2.3",
        bundle="Org.Beeware",
        description="A simple app",
        sources=["src/MyApp", "somewhere/else/interesting", "local_app"],
        license={"file": "LICENSE"},
    )

    # The basic properties have been set.
    assert config.app_name == "MyApp"
    assert config.bundle == "org.beeware"

    # Derived properties have been set.
    assert config.bundle_name == "myapp"
    assert config.bundle_identifier == "org.beeware.myapp"
    assert config.formal_name == "MyApp"
    assert config.class_name == "MyApp"

    # The object has a meaningful REPL
    assert repr(config) == "<org.beeware.myapp v1.2.3 AppConfig>"
