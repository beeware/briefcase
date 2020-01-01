import pytest

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseConfigError


def test_minimal_AppConfig():
    "A simple config can be defined"
    config = AppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=['src/myapp'],
    )

    # The basic properties have been set.
    assert config.app_name == "myapp"
    assert config.version == '1.2.3'
    assert config.bundle == 'org.beeware'
    assert config.description == 'A simple app'
    assert config.requires is None

    # Derived properties have been set.
    assert config.formal_name == 'myapp'
    assert config.document_types == {}

    # There is no icon or splash of any kind
    assert config.icon is None
    assert config.splash is None

    assert repr(config) == "<org.beeware.myapp v1.2.3 AppConfig>"


def test_extra_attrs():
    "A config can contain attributes in addition to those required"
    config = AppConfig(
        app_name="myapp",
        formal_name="My App",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        template='/path/to/template',
        sources=['src/myapp'],
        requires=['first', 'second', 'third'],
        document_type={
            'document': {
                'extension': 'doc',
                'description': 'A document',
            }
        },
        first="value 1",
        second=42,
    )

    # The basic properties have been set.
    assert config.app_name == "myapp"
    assert config.version == '1.2.3'
    assert config.bundle == 'org.beeware'
    assert config.description == 'A simple app'
    assert config.template == '/path/to/template'
    assert config.requires == ['first', 'second', 'third']

    # Properties that are derived by default have been set explicitly
    assert config.formal_name == 'My App'
    assert config.document_types == {
        'document': {
            'extension': 'doc',
            'description': 'A document',
        }
    }

    # Explicit additional properties have been set
    assert config.first == "value 1"
    assert config.second == 42

    # An attribute that wasn't provided raises an error
    with pytest.raises(AttributeError):
        config.unknown


@pytest.mark.parametrize(
    'name',
    [
        'myapp',  # lowercase
        'myApp',  # contains uppercase
        'MyApp',  # initial uppercase
        'MyAPP',  # ends in uppercase
        'my-app',  # contains hyphen
        'my_app',  # contains underscore
        'myapp2',  # ends with digit
        'my2app',  # contains digit
    ]
)
def test_valid_app_name(name):
    try:
        AppConfig(
            app_name=name,
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=['src/' + name.replace('-', '_')]
        )
    except BriefcaseConfigError:
        pytest.fail('{name} should be valid'.format(name=name))


@pytest.mark.parametrize(
    'name',
    [
        '!myapp',  # initial punctuation
        'my!app',  # contains punctuation
        'myapp!',  # end punctuation
        'my$app',  # other punctuation
        '-myApp',  # initial hyphen
        'myApp-',  # end hyphen
        '_myApp',  # initial underscore
        'myApp_',  # end underscore
    ]
)
def test_invalid_app_name(name):
    with pytest.raises(BriefcaseConfigError, match=r"is not a valid app name\."):
        AppConfig(
            app_name=name,
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=['src/invalid']
        )


def test_valid_app_version():
    try:
        AppConfig(
            app_name="myapp",
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=['src/myapp']
        )
    except BriefcaseConfigError:
        pytest.fail('1.2.3 should be a valid version number')


def test_invalid_app_version():
    with pytest.raises(BriefcaseConfigError, match=r"Version number for myapp.*is not valid\."):
        AppConfig(
            app_name="myapp",
            version="foobar",
            bundle="org.beeware",
            description="A simple app",
            sources=['src/invalid']
        )


@pytest.mark.parametrize(
    'name, module_name',
    [
        ('myapp', 'myapp'),
        ('my-app', 'my_app'),
    ]
)
def test_module_name(name, module_name):
    config = AppConfig(
        app_name=name,
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=['src/' + module_name]
    )

    assert config.module_name == module_name


@pytest.mark.parametrize(
    'sources',
    [
        ['src/dupe', 'src/dupe'],
        ['src/dupe', 'src/other', 'src/dupe'],
        ['src/dupe', 'somewhere/dupe', 'src/other'],
        ['src/dupe', 'src/deep/dupe', 'src/other'],
    ]
)
def test_duplicated_source(sources):
    with pytest.raises(BriefcaseConfigError, match=r"contains duplicated package names\."):
        AppConfig(
            app_name='dupe',
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=sources
        )


def test_no_source_for_app():
    with pytest.raises(BriefcaseConfigError, match=r" does not include a package named 'my_app'\."):
        AppConfig(
            app_name='my-app',
            version="1.2.3",
            bundle="org.beeware",
            description="A simple app",
            sources=['src/something', 'src/other']
        )
