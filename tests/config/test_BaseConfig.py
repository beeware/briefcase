from briefcase.config import BaseConfig


def test_update():
    # Expect update() to overwrite an existing field
    config = BaseConfig()
    config.requires = ["newpackage=1.1"]
    new_requirements = ["newpackage=1.2"]
    config.update({"requires": new_requirements})
    assert config.requires == new_requirements


def test_setdefault():
    config = BaseConfig()
    # Expect setdefault() to add new field since it does not exist
    result = config.setdefault("requires", [])
    assert result == config.requires
    assert config.requires == []

    # Expect setdefault() to not overwrite existing field
    new_requirements = config.requires = ["newpackage=1.2"]
    result = config.setdefault("requires", [])
    assert result == config.requires
    assert config.requires == new_requirements
