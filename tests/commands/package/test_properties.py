def test_packaging_formats(default_package_command):
    assert default_package_command.packaging_formats == ["default"]


def test_default_packaging_format(default_package_command):
    assert default_package_command.default_packaging_format == "default"
