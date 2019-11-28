import pytest

from briefcase.config import AppConfig


def test_minimal_AppConfig():
    "A simple config can be defined"
    config = AppConfig(
        name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
    )

    # The basic properties have been set.
    assert config.name == "myapp"
    assert config.version == '1.2.3'
    assert config.bundle == 'org.beeware'
    assert config.description == 'A simple app'
    assert config.template is None
    assert config.requires is None

    # Derived properties have been set.
    assert config.formal_name == 'myapp'
    assert config.document_types == {}

    # There is no icon or splash of any kind
    assert config.icon is None
    assert config.splash is None

    assert repr(config) == "<AppConfig org.beeware.myapp v1.2.3>"


def test_extra_attrs():
    "A config can contain attributes in addition to those required"
    config = AppConfig(
        name="myapp",
        formal_name="My App",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        template='/path/to/template',
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
    assert config.name == "myapp"
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
    'name, module_name',
    [
        ('myapp', 'myapp'),
        ('my-app', 'my_app'),
    ]
)
def test_module_name(name, module_name):
    config = AppConfig(
        name=name,
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
    )

    assert config.module_name == module_name


@pytest.mark.parametrize(
    'formal_name, class_name',
    [
        ('MyApp', 'MyApp'),
        ('My App', 'MyApp'),
    ]
)
def test_class_name(formal_name, class_name):
    config = AppConfig(
        name='myapp',
        formal_name=formal_name,
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
    )

    assert config.class_name == class_name
